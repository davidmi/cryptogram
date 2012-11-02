// Copyright 2012. The Cryptogram Authors. BSD-Style License.
// Author: tierney@cs.nyu.edu (Matt Tierney)

#ifndef _AESTHETE_THREAD_H_
#define _AESTHETE_THREAD_H_

#include <bitset>
#include <fstream>
#include <iostream>
#include <pthread.h>

#include "queue.h"
#include "types.h"

typedef vector<bitset<48> >* MatrixQueueEntry;

namespace cryptogram {

class AestheteRunner {
 public:
  AestheteRunner(int i, Queue* queue);
  virtual ~AestheteRunner();

  void Start();
  void Done();
  void Join();
  
  static void* Run(void* context);

  Queue* queue() { return queue_; }
  int get_i() { return i_; }

 private:
  int i_;
  bool done_;
  pthread_t thread_;
  Queue* queue_;

  DISALLOW_COPY_AND_ASSIGN(AestheteRunner);
};

// AestheteReader aims to read data off of disk and push chunks of that data
// into a queue that will be accessible to multiple processing threads.
class AestheteReader {
 public:
  AestheteReader(const string& filename, int i, Queue* queue);
  virtual ~AestheteReader();

  void Start();
  void Done();
  void Join();
  
  static void* Run(void* context);
  Queue* queue() { return queue_; }
  
 private:
  string filename_;
  int i_;
  bool done_;
  pthread_t thread_;
  Queue* queue_;
  
  DISALLOW_COPY_AND_ASSIGN(AestheteReader);
};

} // namespace cryptogram

#endif  // _AESTHETE_THREAD_H_
