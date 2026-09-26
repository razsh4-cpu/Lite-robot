#include "body_shift_load_proxy.hpp"
#include "json.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

using json = nlohmann::json;

namespace {

struct Sample {
  double timestamp{};
  std::string phase;
  std::array<double, 4> fz{};
};

double Quantile(std::vector<double> values, double fraction) {
  if (values.empty()) throw std::runtime_error("empty statistic");
  std::sort(values.begin(), values.end());
  const double index = fraction * static_cast<double>(values.size() - 1);
  const auto lower = static_cast<size_t>(std::floor(index));
  const auto upper = static_cast<size_t>(std::ceil(index));
  const double alpha = index - static_cast<double>(lower);
  return values[lower] + alpha * (values[upper] - values[lower]);
}

double Median(const std::vector<double>& values) {
  return Quantile(values, 0.5);
}

std::array<double, 12> ReadJoints(const json& record, const char* field) {
  const auto values = record.at(field).get<std::vector<double>>();
  if (values.size() != 12)
    throw std::runtime_error(std::string(field) + " must contain 12 values");
  std::array<double, 12> result{};
  std::copy(values.begin(), values.end(), result.begin());
  return result;
}

std::vector<Sample> Load(const std::string& path) {
  std::ifstream input(path);
  if (!input) throw std::runtime_error("cannot open JSONL trace: " + path);
  std::vector<Sample> samples;
  std::string line;
  size_t line_number = 0;
  while (std::getline(input, line)) {
    ++line_number;
    if (line.empty()) continue;
    const auto record = json::parse(line);
    if (!record.contains("phase") || record.value("reason", "") != "SENT")
      continue;
    try {
      Sample sample;
      sample.timestamp = record.at("timestamp_s").get<double>();
      sample.phase = record.at("phase").get<std::string>();
      sample.fz = body_shift_load::VerticalLoadProxy(
          ReadJoints(record, "position"), ReadJoints(record, "torque"));
      samples.push_back(sample);
    } catch (const std::exception& error) {
      throw std::runtime_error("line " + std::to_string(line_number) +
                               ": " + error.what());
    }
  }
  if (samples.empty()) throw std::runtime_error("trace has no SENT samples");
  return samples;
}

std::array<std::vector<double>, 4> Values(
    const std::vector<Sample>& samples, const std::string& phase) {
  std::array<std::vector<double>, 4> values;
  for (const auto& sample : samples) {
    if (sample.phase != phase) continue;
    for (int leg = 0; leg < 4; ++leg) values[leg].push_back(sample.fz[leg]);
  }
  return values;
}

double StandardDeviation(const std::vector<double>& values) {
  const double mean = std::accumulate(values.begin(), values.end(), 0.0) /
                      static_cast<double>(values.size());
  double sum = 0.0;
  for (double value : values) sum += (value - mean) * (value - mean);
  return std::sqrt(sum / static_cast<double>(values.size()));
}

std::array<double, 4> WindowMedians(const std::vector<double>& values) {
  if (values.size() < 4) throw std::runtime_error("too few baseline samples");
  std::array<double, 4> result{};
  for (size_t window = 0; window < 4; ++window) {
    const size_t begin = window * values.size() / 4;
    const size_t end = (window + 1) * values.size() / 4;
    result[window] = Median(std::vector<double>(values.begin() + begin,
                                                values.begin() + end));
  }
  return result;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 2)
      throw std::runtime_error("usage: body_shift_load_analyzer TRACE.jsonl");
    const auto samples = Load(argv[1]);
    const auto reverse_settle_values =
        Values(samples, "BODY_SHIFT_SAFE_30_REVERSE_Y_SETTLE");
    const auto refined_settle_values =
        Values(samples, "BODY_SHIFT_SAFE_30_REFINED_X_SETTLE");
    const auto zero_x_settle_values =
        Values(samples, "BODY_SHIFT_SAFE_30_ZERO_X_SETTLE");
    const auto y5_settle_values = Values(samples, "BODY_SHIFT_Y5_SETTLE");
    const auto y65_settle_values = Values(samples, "BODY_SHIFT_Y65_SETTLE");
    const auto x4y5_settle_values = Values(samples, "BODY_SHIFT_X4_Y5_SETTLE");
    const auto roll025_settle_values =
        Values(samples, "BODY_SHIFT_X2_Y5_ROLL025_SETTLE");
    const auto support05_settle_values =
        Values(samples, "BODY_SHIFT_X2_Y5_SUPPORT05_SETTLE");
    const auto support075_settle_values =
        Values(samples, "BODY_SHIFT_X2_Y5_SUPPORT075_SETTLE");
    const auto physical_c1_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_C1_SETTLE");
    const auto physical_c2_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_C2_SETTLE");
    const auto physical_c3_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_C3_SETTLE");
    const auto physical_pitch_n025_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_PITCH_N025_SETTLE");
    const auto physical_pitch_p025_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_PITCH_P025_SETTLE");
    const auto physical_height_p05_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_HEIGHT_P05_SETTLE");
    const auto physical_geom_expand_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_GEOM_EXPAND_SETTLE");
    const auto physical_force_opt1_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_FORCE_OPT1_SETTLE");
    const auto physical_balanced_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_BALANCED_SETTLE");
    const auto physical_force_opt2_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_FORCE_OPT2_SETTLE");
    const auto physical_force_opt3_settle_values =
        Values(samples, "BODY_SHIFT_PHYS_FORCE_OPT3_SETTLE");
    const auto settle_values = Values(samples, "BODY_SHIFT_SAFE_30_SETTLE");
    const std::string baseline_phase = !physical_force_opt3_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_FORCE_OPT3_SETTLE"
        : !physical_force_opt2_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_FORCE_OPT2_SETTLE"
        : !physical_balanced_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_BALANCED_SETTLE"
        : !physical_force_opt1_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_FORCE_OPT1_SETTLE"
        : !physical_geom_expand_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_GEOM_EXPAND_SETTLE"
        : !physical_height_p05_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_HEIGHT_P05_SETTLE"
        : !physical_pitch_p025_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_PITCH_P025_SETTLE"
        : !physical_pitch_n025_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_PITCH_N025_SETTLE"
        : !physical_c1_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_C1_SETTLE"
        : !physical_c2_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_C2_SETTLE"
        : !physical_c3_settle_values[0].empty()
        ? "BODY_SHIFT_PHYS_C3_SETTLE"
        : !support075_settle_values[0].empty()
        ? "BODY_SHIFT_X2_Y5_SUPPORT075_SETTLE"
        : !support05_settle_values[0].empty()
        ? "BODY_SHIFT_X2_Y5_SUPPORT05_SETTLE"
        : !roll025_settle_values[0].empty()
        ? "BODY_SHIFT_X2_Y5_ROLL025_SETTLE"
        : !x4y5_settle_values[0].empty()
        ? "BODY_SHIFT_X4_Y5_SETTLE"
        : !y65_settle_values[0].empty()
        ? "BODY_SHIFT_Y65_SETTLE"
        : !y5_settle_values[0].empty()
        ? "BODY_SHIFT_Y5_SETTLE"
        : !zero_x_settle_values[0].empty()
        ? "BODY_SHIFT_SAFE_30_ZERO_X_SETTLE"
        : !refined_settle_values[0].empty()
        ? "BODY_SHIFT_SAFE_30_REFINED_X_SETTLE"
        : !reverse_settle_values[0].empty()
        ? "BODY_SHIFT_SAFE_30_REVERSE_Y_SETTLE"
        : !settle_values[0].empty()
            ? "BODY_SHIFT_SAFE_30_SETTLE" : "TARGET_REACHED";
    const auto baseline_values = Values(samples, baseline_phase);
    const std::array<const char*, 4> names{{"FL", "FR", "HL", "HR"}};
    std::array<double, 4> baseline{};

    std::cout << std::fixed << std::setprecision(6);
    std::cout << "method=damped_Jt_F_equals_minus_tau damping="
              << body_shift_load::kDamping
              << " units=relative_N_proxy safety_gate=false"
              << " baseline_phase=" << baseline_phase << '\n';
    for (int leg = 0; leg < 4; ++leg) {
      if (baseline_values[leg].empty())
        throw std::runtime_error("no stable stand baseline samples");
      baseline[leg] = Median(baseline_values[leg]);
      std::vector<double> deviations;
      deviations.reserve(baseline_values[leg].size());
      for (double value : baseline_values[leg])
        deviations.push_back(std::abs(value - baseline[leg]));
      const auto windows = WindowMedians(baseline_values[leg]);
      double max_window_drift = 0.0;
      for (double value : windows)
        max_window_drift = std::max(max_window_drift,
                                    std::abs(value - baseline[leg]));
      std::cout << "BASELINE leg=" << names[leg]
                << " samples=" << baseline_values[leg].size()
                << " median_fz_proxy=" << baseline[leg]
                << " mad=" << Median(deviations)
                << " stddev=" << StandardDeviation(baseline_values[leg])
                << " p05=" << Quantile(baseline_values[leg], 0.05)
                << " p95=" << Quantile(baseline_values[leg], 0.95)
                << " quarter_medians=" << windows[0] << ',' << windows[1]
                << ',' << windows[2] << ',' << windows[3]
                << " max_quarter_drift=" << max_window_drift << '\n';
    }

    std::map<std::string, std::array<std::vector<double>, 4>> phases;
    for (const auto& sample : samples)
      for (int leg = 0; leg < 4; ++leg)
        phases[sample.phase][leg].push_back(sample.fz[leg]);
    for (const auto& [phase, values] : phases) {
      std::cout << "PHASE name=" << phase;
      for (int leg = 0; leg < 4; ++leg) {
        if (values[leg].empty()) continue;
        const double median = Median(values[leg]);
        const size_t tail_begin = 3 * values[leg].size() / 4;
        const double tail_median = Median(std::vector<double>(
            values[leg].begin() + tail_begin, values[leg].end()));
        std::cout << ' ' << names[leg] << "_median=" << median
                  << ' ' << names[leg] << "_delta=" << median - baseline[leg]
                  << ' ' << names[leg] << "_percent="
                  << 100.0 * (median - baseline[leg]) / baseline[leg]
                  << ' ' << names[leg] << "_tail_median=" << tail_median
                  << ' ' << names[leg] << "_tail_delta="
                  << tail_median - baseline[leg];
      }
      std::cout << '\n';
    }
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
