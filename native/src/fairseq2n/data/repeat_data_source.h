// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

#pragma once

#include <cstddef>
#include <memory>
#include <optional>
#include <utility>

#include "fairseq2n/data/data_source.h"

namespace fairseq2n::detail {

class repeat_data_source final : public data_source {
public:
    explicit
    repeat_data_source(
        std::unique_ptr<data_source> &&inner, std::optional<std::size_t> num_repeats) noexcept
      : inner_{std::move(inner)}, num_repeats_{num_repeats}
    {}

    std::optional<data>
    next() override;

    void
    reset() override;

    void
    record_position(tape &t, bool strict) const override;

    void
    reload_position(tape &t, bool strict) override;

    bool
    is_infinite() const noexcept override;

private:
    std::unique_ptr<data_source> inner_;
    bool has_data_ = false;
    std::optional<std::size_t> num_repeats_;
    std::size_t repeat_nr_ = 0;
};

}  // namespace fairseq2n::detail
