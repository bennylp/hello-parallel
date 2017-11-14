#!/usr/bin/env python
from __future__ import absolute_import, print_function

import sys
import time

import numpy as np
import pyopencl as cl
import saxpy

def main(where):
    print("PyOpenCL version " + cl.VERSION_TEXT)
    platforms = cl.get_platforms()
    if not platforms:
        raise RuntimeError("No platform found")
    dev_type = cl.device_type.GPU if where == "gpu" else \
               cl.device_type.CPU if where == "cpu" else cl.device_type.ALL
    dev = None
    for plat in platforms:
        devs = plat.get_devices(dev_type)
        if devs:
            dev = devs[0]
            break
    if not dev:
        raise RuntimeError("No matching device found")

    print("Using {}".format(dev.get_info(cl.device_info.NAME)))
    ctx = cl.Context([dev])

    host_x = np.ones([saxpy.N], dtype=np.float32) * saxpy.XVAL
    host_y = np.ones([saxpy.N], dtype=np.float32) * saxpy.YVAL
    print("N: {}".format(len(host_x)))

    dev_x = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=host_x)
    dev_y = cl.Buffer(ctx, cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR, hostbuf=host_y)

    prg = cl.Program(ctx, """
            __kernel void saxpy(float alpha,
                                __global const float* X,
                                __global float* Y)
            {
                int i = get_global_id(0); 
                Y[i] += alpha * X[i];
            }
            """).build()

    queue = cl.CommandQueue(ctx)

    t0 = time.time()
    event = prg.saxpy(queue, host_x.shape, None, np.float32(saxpy.AVAL), dev_x, dev_y)
    event.wait()
    t1 = time.time()
    print("Elapsed: {} ms".format((t1 - t0) * 1000))

    cl.enqueue_read_buffer(queue, dev_y, host_y).wait()
    saxpy.verify(host_y)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
