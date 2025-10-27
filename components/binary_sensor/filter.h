#pragma once

#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "esphome/core/helpers.h"

#include <vector>

namespace esphome {

namespace binary_sensor {

class BinarySensor;

class Filter {
 public:
  virtual optional<bool> new_value(bool value) = 0;

  virtual void input(bool value);

  void output(bool value);

 protected:
  friend BinarySensor;

  Filter *next_{nullptr};
  BinarySensor *parent_{nullptr};
  Deduplicator<bool> dedup_;
};

class TimeoutFilter : public Filter, public Component {
 public:
  optional<bool> new_value(bool value) override { return value; }
  void input(bool value) override;
  template<typename T> void set_timeout_value(T timeout) { this->timeout_delay_ = timeout; }

 protected:
  TemplatableValue<uint32_t> timeout_delay_{};
};

class DelayedOnOffFilter : public Filter, public Component {
 public:
  optional<bool> new_value(bool value) override;

  float get_setup_priority() const override;

  template<typename T> void set_on_delay(T delay) { this->on_delay_ = delay; }
  template<typename T> void set_off_delay(T delay) { this->off_delay_ = delay; }

 protected:
  TemplatableValue<uint32_t> on_delay_{};
  TemplatableValue<uint32_t> off_delay_{};
};

class DelayedOnFilter : public Filter, public Component {
 public:
  optional<bool> new_value(bool value) override;

  float get_setup_priority() const override;

  template<typename T> void set_delay(T delay) { this->delay_ = delay; }

 protected:
  TemplatableValue<uint32_t> delay_{};
};

class DelayedOffFilter : public Filter, public Component {
 public:
  optional<bool> new_value(bool value) override;

  float get_setup_priority() const override;

  template<typename T> void set_delay(T delay) { this->delay_ = delay; }

 protected:
  TemplatableValue<uint32_t> delay_{};
};

class InvertFilter : public Filter {
 public:
  optional<bool> new_value(bool value) override;
};

struct AutorepeatFilterTiming {
  AutorepeatFilterTiming(uint32_t delay, uint32_t off, uint32_t on) {
    this->delay = delay;
    this->time_off = off;
    this->time_on = on;
  }
  uint32_t delay;
  uint32_t time_off;
  uint32_t time_on;
};

class AutorepeatFilter : public Filter, public Component {
 public:
  explicit AutorepeatFilter(std::vector<AutorepeatFilterTiming> timings);

  optional<bool> new_value(bool value) override;

  float get_setup_priority() const override;

 protected:
  void next_timing_();
  void next_value_(bool val);

  std::vector<AutorepeatFilterTiming> timings_;
  uint8_t active_timing_{0};
};

class LambdaFilter : public Filter {
 public:
  explicit LambdaFilter(std::function<optional<bool>(bool)> f);

  optional<bool> new_value(bool value) override;

 protected:
  std::function<optional<bool>(bool)> f_;
};

class SettleFilter : public Filter, public Component {
 public:
  optional<bool> new_value(bool value) override;

  float get_setup_priority() const override;

  template<typename T> void set_delay(T delay) { this->delay_ = delay; }

 protected:
  TemplatableValue<uint32_t> delay_{};
  bool steady_{true};
};

}  // namespace binary_sensor

}  // namespace esphome
