# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import annotations

from typing import Any, Dict, Optional

import torch
from torch import Tensor
from torcheval.metrics import Mean, Sum

from fairseq2.gang import Gang
from fairseq2.metrics import MetricBag
from fairseq2.models.seq2seq import Seq2SeqBatch
from fairseq2.models.sequence import SequenceBatch


class SequenceModelMetricBag(MetricBag):
    """Holds the training metrics of a sequence model."""

    _nll_loss: Mean
    _batch_size: Mean
    _elements_per_batch: Mean
    _num_examples: Sum
    _num_elements: Sum
    _num_target_elements: Sum
    _total_num_examples: Sum
    _total_num_elements: Sum
    _total_num_target_elements: Sum

    def __init__(self, gang: Gang) -> None:
        """
        :param gang:
            The gang over which to sync metrics.
        """
        super().__init__(gang)

        d = gang.device

        self.register_metric("_nll_loss", Mean(device=d), persistent=False)

        self.register_metric("_batch_size", Mean(device=d), persistent=False)

        self.register_metric("_elements_per_batch", Mean(device=d), persistent=False)

        self.register_metric("_num_examples", Sum(device=d), persistent=False)

        self.register_metric("_num_elements", Sum(device=d), persistent=False)

        self.register_metric("_num_target_elements", Sum(device=d), persistent=False)

        self._total_num_examples = Sum(device=d)

        self._total_num_elements = Sum(device=d)

        self._total_num_target_elements = Sum(device=d)

    @torch.inference_mode()
    def update_loss_metrics(self, batch: SequenceBatch, nll_loss: Tensor) -> None:
        """Update the loss metrics.

        :param batch:
            The batch processed by the model.
        :param nll_loss:
            The loss of ``batch``.
        """
        batch_size = torch.tensor(batch.batch_size)

        num_elements = torch.tensor(batch.num_elements())
        num_target_elements = torch.tensor(batch.num_target_elements())

        normalized_nll_loss = nll_loss.cpu() / num_target_elements

        self._nll_loss.update(normalized_nll_loss, weight=num_target_elements)

        self._batch_size.update(batch_size * self._gang.size)

        self._elements_per_batch.update(num_elements * self._gang.size)

        self._num_examples.update(batch_size)

        self._num_elements.update(num_elements)

        self._num_target_elements.update(num_target_elements)

        self._total_num_examples.update(batch_size)

        self._total_num_elements.update(num_elements)

        self._total_num_target_elements.update(num_target_elements)


class Seq2SeqModelMetricBag(MetricBag):
    """Holds the training metrics of a sequence-to-sequence model."""

    _nll_loss: Mean
    _batch_size: Mean
    _elements_per_batch: Mean
    _num_examples: Sum
    _num_source_elements: Sum
    _num_target_elements: Sum
    _total_num_examples: Sum
    _total_num_source_elements: Sum
    _total_num_target_elements: Sum

    def __init__(self, gang: Gang) -> None:
        """
        :param gang:
            The gang over which to sync metrics.
        """
        super().__init__(gang)

        d = gang.device

        self.register_metric("_nll_loss", Mean(device=d), persistent=False)

        self.register_metric("_batch_size", Mean(device=d), persistent=False)

        self.register_metric("_elements_per_batch", Mean(device=d), persistent=False)

        self.register_metric("_num_examples", Sum(device=d), persistent=False)

        self.register_metric("_num_source_elements", Sum(device=d), persistent=False)
        self.register_metric("_num_target_elements", Sum(device=d), persistent=False)

        self._total_num_examples = Sum(device=d)

        self._total_num_source_elements = Sum(device=d)
        self._total_num_target_elements = Sum(device=d)

    @torch.inference_mode()
    def update_loss_metrics(self, batch: Seq2SeqBatch, nll_loss: Tensor) -> None:
        """Update the loss metrics.

        :param batch:
            The batch processed by the model.
        :param nll_loss:
            The loss of ``batch``.
        """
        batch_size = torch.tensor(batch.batch_size)

        num_source_elements = torch.tensor(batch.num_source_elements())
        num_target_elements = torch.tensor(batch.num_target_elements())

        normalized_nll_loss = nll_loss.cpu() / num_target_elements

        self._nll_loss.update(normalized_nll_loss, weight=num_target_elements)

        self._batch_size.update(batch_size * self._gang.size)

        self._elements_per_batch.update(num_target_elements * self._gang.size)

        self._num_examples.update(batch_size)

        self._num_source_elements.update(num_source_elements)
        self._num_target_elements.update(num_target_elements)

        self._total_num_examples.update(batch_size)

        self._total_num_source_elements.update(num_source_elements)
        self._total_num_target_elements.update(num_target_elements)


def compute_throughput(
    metric_values: Dict[str, Any],
    throughput_metric_name: Optional[str],
    elapsed_time: float,
) -> None:
    """Computes the task throughput.

    :param metric_values:
        The metric values computed by a :class:`MetricBag`.
    :param throughput_metric_name:
        The name of the throughput metric (e.g. num_elements).
    :param elapsed_time:
        The time elapsed since the last throughput call.
    """
    if throughput_metric_name is None:
        return

    try:
        num_elements = metric_values[throughput_metric_name]
    except KeyError:
        return

    if not isinstance(num_elements, (int, float, Tensor)):
        return

    if elapsed_time == 0.0:
        metric_values["elements_per_second"] = 0.0
    else:
        metric_values["elements_per_second"] = num_elements / elapsed_time
