// Copyright (c) 2011 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "base/test/signaling_task.h"

#include "base/synchronization/waitable_event.h"

namespace base {

SignalingTask::SignalingTask(base::WaitableEvent* event) : event_(event) {
}

SignalingTask::~SignalingTask() {}

void SignalingTask::Run() {
  event_->Signal();
}

}  // namespace base
