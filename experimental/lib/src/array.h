// Copyright 2012. The Cryptogram Authors. BSD License.
// Author: tierney@cs.nyu.edu (Matt Tierney)

#ifndef _CRYPTOGRAM_ARRAY_H_
#define _CRYPTOGRAM_ARRAY_H_

#include "glog/logging.h"
#include "boost/numeric/ublas/matrix.hpp"
#include "ecc_image.h"

using boost::numeric::ublas::matrix;

namespace cryptogram {

template<typename T>
struct array {
  T* data;
  int w, h;

  array() : data(NULL), w(0), h(0) {}

  array(int width, int height) {
    data = new T[width * height];
    w = width;
    h = height;
  }

  ~array() {
    delete[] data;
  }

  T& operator()(int x, int y) {
    return data[y * w + x];
  }

  void RandomAesthete(const std::vector<int>& values);
  void FillFromInts(const std::vector<int>& indices,
                    const std::vector<int>& values);
  void FillBlockFromInts(const std::vector<int>& indices,
                         const std::vector<int>& values,
                         int block_h,
                         int block_w);
  void FillMatrixFromBlock(int block_h,
                           int block_w,
                           matrix<unsigned char>* lum_matrix);
};

} // namespace cryptogram

#endif  // _CRYPTOGRAM_ARRAY_H_
