# Copyright 2020 MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np

from monai.transforms import Resize
from monai.utils import ensure_tuple_rep, min_version, optional_import

Image, _ = optional_import("PIL", name="Image")


def write_png(data, file_name: str, output_shape=None, interp_order: str = "bicubic", scale=None):
    """
    Write numpy data into png files to disk.
    Spatially it supports HW for 2D.(H,W) or (H,W,3) or (H,W,4).
    If `scale` is None, expect the input data in `np.uint8` or `np.uint16` type.
    It's based on the Image module in PIL library:
    https://pillow.readthedocs.io/en/stable/reference/Image.html

    Args:
        data (numpy.ndarray): input data to write to file.
        file_name: expected file name that saved on disk.
        output_shape (None or tuple of ints): output image shape.
        interp_order (`nearest|linear|bilinear|bicubic|trilinear|area`):
            the interpolation mode. Default="bicubic".
            See also: https://pytorch.org/docs/stable/nn.functional.html#interpolate
        scale (255, 65535): postprocess data by clipping to [0, 1] and scaling to
            [0, 255] (uint8) or [0, 65535] (uint16). Default is None to disable scaling.

    """
    assert isinstance(data, np.ndarray), "input data must be numpy array."
    if len(data.shape) == 3 and data.shape[2] == 1:  # PIL Image can't save image with 1 channel
        data = data.squeeze(2)
    if output_shape is not None:
        output_shape = ensure_tuple_rep(output_shape, 2)
        align_corners = False if interp_order in ("linear", "bilinear", "bicubic", "trilinear") else None
        xform = Resize(spatial_size=output_shape, interp_order=interp_order, align_corners=align_corners)
        _min, _max = np.min(data), np.max(data)
        if len(data.shape) == 3:
            data = np.moveaxis(data, -1, 0)  # to channel first
            data = xform(data)
            data = np.moveaxis(data, 0, -1)
        else:  # (H, W)
            data = np.expand_dims(data, 0)  # make a channel
            data = xform(data)[0]  # first channel
        if interp_order != "nearest":
            data = np.clip(data, _min, _max)

    if scale is not None:
        data = np.clip(data, 0.0, 1.0)  # png writer only can scale data in range [0, 1]
        if scale == np.iinfo(np.uint8).max:
            data = (scale * data).astype(np.uint8)
        elif scale == np.iinfo(np.uint16).max:
            data = (scale * data).astype(np.uint16)
        else:
            raise ValueError(f"unsupported scale value: {scale}.")

    img = Image.fromarray(data)
    img.save(file_name, "PNG")
    return
