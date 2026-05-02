"""
Test runner engine with multi-layer orchestration.
"""

import logging
import time
from typing import Dict, List, Optional, Type

from src.core.layer import LayerContext, LayerProtocol, LayerResult, TestStatus


logger = logging.getLogger(__name__)


class TestRunnerEngine:
    """
    Orchestrates multi-layer test execution.

    Manages layer registration, execution order, and result aggregation.
    """

    def __init__(self, config: Optional[Dict] = None):
        self._layers: Dict[str, LayerProtocol] = {}
        self._execution_order: List[str] = []
        self._config = config or {}
        self._results: Dict[str, LayerResult] = {}
        self._logger = logging.getLogger(__name__)

    def register_layer(self, layer: LayerProtocol, position: Optional[int] = None) -> None:
        """
        Register a layer with the runner.

        Args:
            layer: Layer instance implementing LayerProtocol
            position: Optional position in execution order (append if None)
        """
        self._layers[layer.name] = layer
        if position is None:
            self._execution_order.append(layer.name)
        else:
            self._execution_order.insert(position, layer.name)
        self._logger.info(f"Registered layer: {layer.name}")

    def unregister_layer(self, layer_name: str) -> None:
        """Remove a layer from the runner."""
        if layer_name in self._layers:
            del self._layers[layer_name]
            self._execution_order.remove(layer_name)
            self._logger.info(f"Unregistered layer: {layer_name}")

    def get_layer(self, layer_name: str) -> Optional[LayerProtocol]:
        """Get a registered layer by name."""
        return self._layers.get(layer_name)

    def get_registered_layers(self) -> List[str]:
        """Get list of registered layer names in execution order."""
        return self._execution_order.copy()

    def run_all_layers(self, context: LayerContext) -> Dict[str, LayerResult]:
        """
        Execute all registered layers in order.

        Args:
            context: Initial layer context

        Returns:
            Dictionary mapping layer names to their results
        """
        self._results = {}
        self._logger.info(f"Starting test run with {len(self._layers)} layers")

        # Build context chain for hierarchical propagation
        current_context = context
        for i, layer_name in enumerate(self._execution_order):
            layer = self._layers[layer_name]

            # Set parent reference for cross-layer context propagation
            if i > 0:
                prev_layer_name = self._execution_order[i - 1]
                if prev_layer_name in self._results:
                    parent_result = self._results[prev_layer_name]
                    # Create child context with parent reference
                    current_context = LayerContext(
                        layer_name=layer_name,
                        server=context.server,
                        hardware=context.hardware,
                        components=context.components,
                        parent=current_context,
                        test_data={},
                        logger=context.logger,
                    )

            self._logger.info(f"Executing layer: {layer_name}")

            # Setup phase
            start_time = time.time()
            try:
                layer.setup(current_context)
            except Exception as e:
                self._logger.error(f"Layer {layer_name} setup failed: {e}")
                self._results[layer_name] = LayerResult(
                    layer_name=layer_name,
                    status=TestStatus.ERROR,
                    message=f"Setup failed: {e}",
                    duration_seconds=time.time() - start_time,
                    errors=[str(e)],
                )
                continue

            # Execute phase
            try:
                result = layer.execute(current_context)
                result.duration_seconds = time.time() - start_time
                self._results[layer_name] = result
            except Exception as e:
                self._logger.error(f"Layer {layer_name} execution failed: {e}")
                self._results[layer_name] = LayerResult(
                    layer_name=layer_name,
                    status=TestStatus.ERROR,
                    message=f"Execution failed: {e}",
                    duration_seconds=time.time() - start_time,
                    errors=[str(e)],
                )
                continue

            # Teardown phase
            try:
                layer.teardown(current_context)
            except Exception as e:
                self._logger.warning(f"Layer {layer_name} teardown failed: {e}")
                if self._results[layer_name].status == TestStatus.PASSED:
                    self._results[layer_name].errors.append(f"Teardown warning: {e}")

        self._logger.info("Test run completed")
        return self._results

    def run_layer(self, layer_name: str, context: LayerContext) -> LayerResult:
        """
        Execute a single layer by name.

        Args:
            layer_name: Name of the layer to execute
            context: Layer context

        Returns:
            LayerResult from the execution
        """
        if layer_name not in self._layers:
            return LayerResult(
                layer_name=layer_name,
                status=TestStatus.ERROR,
                message=f"Layer not found: {layer_name}",
            )

        layer = self._layers[layer_name]
        start_time = time.time()

        try:
            layer.setup(context)
            result = layer.execute(context)
            result.duration_seconds = time.time() - start_time
            return result
        except Exception as e:
            return LayerResult(
                layer_name=layer_name,
                status=TestStatus.ERROR,
                message=str(e),
                duration_seconds=time.time() - start_time,
                errors=[str(e)],
            )
        finally:
            try:
                layer.teardown(context)
            except Exception as teardown_err:
                self._logger.warning(f"Teardown error in {layer_name}: {teardown_err}")

    def get_results(self) -> Dict[str, LayerResult]:
        """Get results from the last run."""
        return self._results.copy()

    def get_aggregate_summary(self) -> Dict[str, int]:
        """Get aggregate counts across all layers."""
        total_run = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0

        for result in self._results.values():
            total_run += result.tests_run
            total_passed += result.tests_passed
            total_failed += result.tests_failed
            total_skipped += result.tests_skipped
            total_errors += len(result.errors)

        return {
            "total_run": total_run,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "total_errors": total_errors,
            "layers_executed": len(self._results),
        }
