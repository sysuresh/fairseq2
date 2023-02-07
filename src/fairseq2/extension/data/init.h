// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

#pragma once

#include "fairseq2/extension/pybind11.h"

namespace fairseq2 {

void
def_data(pybind11::module_ &base);

}