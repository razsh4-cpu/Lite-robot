#pragma once

#include "../tools/lite3_leg_kinematics.hpp"

#include <Eigen/Core>

#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
#include <utility>
#include <vector>

// One-use body-only 30/60/90%-of-safe calibration trajectory. All four Cartesian foot
// targets stay at their nominal height; this planner has no unload/lift phase.
class SupportedBodyShiftPlan {
public:
    enum class GainStrategy { AbruptReduced, KeepStand, SmoothReduced };
    enum class RunMode {
        FullSequence, Level30Only, Level60Only, Level90Only,
        Level30ReverseYOnly, Level30RefinedXOnly, Level30ZeroXOnly,
        LevelY5Only, LevelY65Only, LevelX4Y5Only,
        LevelX2Y5Roll025Only, LevelX2Y5Support05Only,
        LevelX2Y5Support075Only, PhysicalCandidate1Only,
        PhysicalCandidate2Only, PhysicalCandidate3Only,
        PhysicalPitchN025Only, PhysicalPitchP025Only,
        PhysicalHeightP05Only, PhysicalGeometryExpandOnly,
        PhysicalForceOpt1Only, PhysicalBalancedOnly, PhysicalForceOpt2Only,
        PhysicalForceOpt3Only, PhysicalLargeLeanOnly,
        PhysicalStagedSupportTriangleOnly
    };

    enum class Phase {
        Settle30, Shift30, Hold30, Recenter30,
        Settle60, Shift60, Hold60, Recenter60,
        Settle90, Shift90, Hold90, Recenter90,
        Settle30ReverseY, Shift30ReverseY, Hold30ReverseY,
        Recenter30ReverseY,
        Settle30RefinedX, Shift30RefinedX, Hold30RefinedX,
        Recenter30RefinedX,
        Settle30ZeroX, Shift30ZeroX, Hold30ZeroX, Recenter30ZeroX,
        SettleY5, ShiftY5, HoldY5, RecenterY5,
        SettleY65, ShiftY65, HoldY65, RecenterY65,
        SettleX4Y5, ShiftX4Y5, HoldX4Y5, RecenterX4Y5,
        SettleX2Y5Roll025, ShiftX2Y5Roll025, HoldX2Y5Roll025,
        RecenterX2Y5Roll025,
        SettleX2Y5Support05, ShiftX2Y5Support05, HoldX2Y5Support05,
        RecenterX2Y5Support05,
        SettleX2Y5Support075, ShiftX2Y5Support075, HoldX2Y5Support075,
        RecenterX2Y5Support075,
        SettlePhysicalCandidate1, ShiftPhysicalCandidate1,
        HoldPhysicalCandidate1, RecenterPhysicalCandidate1,
        SettlePhysicalCandidate2, ShiftPhysicalCandidate2,
        HoldPhysicalCandidate2, RecenterPhysicalCandidate2,
        SettlePhysicalCandidate3, ShiftPhysicalCandidate3,
        HoldPhysicalCandidate3, RecenterPhysicalCandidate3,
        SettlePhysicalPitchN025, ShiftPhysicalPitchN025,
        HoldPhysicalPitchN025, RecenterPhysicalPitchN025,
        SettlePhysicalPitchP025, ShiftPhysicalPitchP025,
        HoldPhysicalPitchP025, RecenterPhysicalPitchP025,
        SettlePhysicalHeightP05, ShiftPhysicalHeightP05,
        HoldPhysicalHeightP05, RecenterPhysicalHeightP05,
        SettlePhysicalGeometryExpand, ShiftPhysicalGeometryExpand,
        HoldPhysicalGeometryExpand, RecenterPhysicalGeometryExpand,
        SettlePhysicalForceOpt1, ShiftPhysicalForceOpt1,
        HoldPhysicalForceOpt1, RecenterPhysicalForceOpt1,
        SettlePhysicalBalanced, ShiftPhysicalBalanced,
        HoldPhysicalBalanced, RecenterPhysicalBalanced,
        SettlePhysicalForceOpt2, ShiftPhysicalForceOpt2,
        HoldPhysicalForceOpt2, RecenterPhysicalForceOpt2,
        SettlePhysicalForceOpt3, ShiftPhysicalForceOpt3,
        HoldPhysicalForceOpt3, RecenterPhysicalForceOpt3,
        SettlePhysicalLargeLean, ShiftPhysicalLargeLean,
        HoldPhysicalLargeLean, RecenterPhysicalLargeLean,
        StagedSettle,
        StagedFLUnload, StagedFLLift, StagedFLMove, StagedFLLower, StagedFLSettle,
        StagedHLUnload, StagedHLLift, StagedHLMove, StagedHLLower, StagedHLSettle,
        StagedHRUnload, StagedHRLift, StagedHRMove, StagedHRLower, StagedHRSettle,
        StagedFinalShift, StagedFinalHold, StagedBodyRecenter,
        StagedRestoreHRUnload, StagedRestoreHRLift, StagedRestoreHRMove,
        StagedRestoreHRLower, StagedRestoreHRSettle,
        StagedRestoreHLUnload, StagedRestoreHLLift, StagedRestoreHLMove,
        StagedRestoreHLLower, StagedRestoreHLSettle,
        StagedRestoreFLUnload, StagedRestoreFLLift, StagedRestoreFLMove,
        StagedRestoreFLLower, StagedRestoreFLSettle, StagedFinalStand,
        Complete
    };

    struct Sample {
        Eigen::Matrix<float,12,5> command =
            Eigen::Matrix<float,12,5>::Zero();
        Phase phase{Phase::Settle30};
        bool complete{false};
    };

    // Requested reference is a BODY translation. Each planted-foot target is
    // recomputed as nominal_foot - level * reference_body_translation.
    static constexpr double kReferenceShiftXM = -0.029043;
    static constexpr double kReferenceShiftYM =  0.026558;
    static constexpr std::array<double,3> kSafeFractions{{0.30,0.60,0.90}};

    static constexpr double kSettleSeconds = 1.0;
    static constexpr double kShiftSeconds = 5.2;
    // Candidate-only slowdown after the first Low-friction physical run showed
    // a late contact/PD settling transient. Endpoint, quintic shape and gains
    // remain unchanged.
    static constexpr double kPhysicalForceOptShiftSeconds = 8.0;
    static constexpr double kPhysicalForceOptRecenterSeconds = 12.0;
    static constexpr double kPhysicalForceOpt2ShiftSeconds = 12.0;
    static constexpr double kPhysicalForceOpt2RecenterSeconds = 16.0;
    static constexpr double kPhysicalLargeLeanShiftSeconds = 25.0;
    static constexpr double kPhysicalLargeLeanRecenterSeconds = 35.0;
    static constexpr double kStagedUnloadSeconds = 4.0;
    static constexpr double kStagedHLUnloadSeconds = 6.0;
    static constexpr double kStagedLiftSeconds = 1.5;
    static constexpr double kStagedMoveSeconds = 3.0;
    static constexpr double kStagedLowerSeconds = 1.5;
    static constexpr double kStagedSettleSeconds = 1.0;
    static constexpr double kStagedBodyShiftSeconds = 8.0;
    static constexpr double kStagedRecenterHalfSeconds = 4.0;
    static constexpr double kStagedMidShiftSettleSeconds = 1.0;
    static constexpr double kStagedFinalStandSeconds = 6.0;
    static constexpr double kStagedFootClearanceM = 0.003;
    static constexpr double kHoldSeconds = 2.0;
    static constexpr double kRecenterSeconds = 5.2;
    static constexpr double kLevelSeconds =
        kSettleSeconds+kShiftSeconds+kHoldSeconds+kRecenterSeconds;
    static constexpr double kTotalSeconds = 3.0*kLevelSeconds;
    static constexpr double kGainRampSeconds = 0.5;
    static constexpr double kVerifyStandSeconds = 2.5;
    static constexpr double kRefinedShiftXM = -0.0020000;
    static constexpr double kRefinedShiftYM = -0.0018299;
    static constexpr double kZeroXShiftXM = 0.0;
    static constexpr double kZeroXShiftYM = -0.0018299;
    static constexpr double kY5ShiftXM = -0.0020000;
    static constexpr double kY5ShiftYM = -0.0050000;
    static constexpr double kY65ShiftXM = -0.0020000;
    static constexpr double kY65ShiftYM = -0.0065000;
    static constexpr double kX4Y5ShiftXM = -0.0040000;
    static constexpr double kX4Y5ShiftYM = -0.0050000;
    static constexpr double kX2Y5Roll025ShiftXM = -0.0020000;
    static constexpr double kX2Y5Roll025ShiftYM = -0.0050000;
    static constexpr double kX2Y5Roll025Rad =
        -0.25*3.14159265358979323846/180.0;
    static constexpr double kX2Y5Support05ShiftXM = -0.0020000;
    static constexpr double kX2Y5Support05ShiftYM = -0.0050000;
    static constexpr std::array<double,4> kX2Y5SupportExtensionM{{
        0.0005,0.0,0.0,0.0005}};
    static constexpr std::array<double,4> kX2Y5Support075ExtensionM{{
        0.00075,0.0,0.0,0.00075}};
    static constexpr std::array<double,4> kPhysicalCandidate1ExtensionM{{
        0.00100,0.0,0.0,0.00100}};
    static constexpr std::array<double,4> kPhysicalCandidate2ExtensionM{{
        0.00125,0.0,0.0,0.00100}};
    static constexpr std::array<double,4> kPhysicalCandidate3ExtensionM{{
        0.00125,0.0,0.0,0.00125}};
    static constexpr double kPhysicalPitchN025Rad =
        -0.25*3.14159265358979323846/180.0;
    static constexpr double kPhysicalPitchP025Rad =
         0.25*3.14159265358979323846/180.0;
    static constexpr std::array<double,4> kPhysicalHeightP05ExtensionM{{
        0.00150,0.00050,0.00050,0.00150}};
    static constexpr std::array<std::array<double,3>,4>
        kPhysicalGeometryExpandOffsetM{{
            {{ 0.0020, 0.0015,0.0}},
            {{ 0.0,    0.0,   0.0}},
            {{-0.0020, 0.0015,0.0}},
            {{-0.0020,-0.0015,0.0}}}};
    static constexpr std::array<std::array<double,3>,4>
        kPhysicalForceOpt1Q{{
            {{ 0.00632858,-0.75172162,1.47242728}},
            {{-0.0167054439148,-0.77216783713,1.51175805905}},
            {{-0.01707707,-0.76241208,1.50300447}},
            {{-0.02225601,-0.77474549,1.48768409}}}};
    static constexpr std::array<std::array<double,3>,4>
        kPhysicalBalancedQ{{
            {{ 0.00719844,-0.75150758,1.47061913}},
            {{-0.0167054439148,-0.77216783713,1.51175805905}},
            {{-0.01697933,-0.76077520,1.50439662}},
            {{-0.02199410,-0.77565856,1.48483468}}}};
    static constexpr std::array<std::array<double,3>,4>
        kPhysicalForceOpt2Q{{
            {{ 0.02400000,-0.74897953,1.48877879}},
            {{ 0.00455403,-0.74902766,1.49676761}},
            {{ 0.02043046,-0.74973161,1.51624438}},
            {{-0.01323031,-0.74897953,1.47650035}}}};
    static constexpr std::array<std::array<double,3>,4>
        kPhysicalForceOpt3Q{{
            {{-0.024299096505,-0.759888805242,1.473223518359}},
            {{-0.024422283795,-0.773094561530,1.498466216521}},
            {{-0.024550385820,-0.774774886517,1.501744331328}},
            {{-0.024492295561,-0.779558889389,1.510881397003}}}};
    // One-use, body-only large-pose identification target. It represents a
    // -30 mm X / -25 mm Y body translation, -2 degree roll and -2 degree
    // pitch, with the previously tested FL/HR support extensions retained.
    // This is deliberately separate from the 0.03-rad calibration modes.
    static constexpr std::array<std::array<double,3>,4>
        kPhysicalLargeLeanQ{{
            {{-0.115346035671,-0.651753680867,1.386078585201}},
            {{-0.116505019629,-0.698275921138,1.480210774755}},
            {{-0.119065894876,-0.698685080701,1.482467953121}},
            {{-0.119517220868,-0.737292999462,1.560953685317}}}};

    static constexpr float kStandKp = 100.0f;
    static constexpr float kStandKd = 2.5f;
    static constexpr float kReducedKp = 60.0f;
    static constexpr float kReducedKd = 0.7f;

    // Existing reviewed body-shift command limits. Calibration does not expand
    // them; an out-of-envelope IK result fails construction and tests.
    static constexpr double kMaxJointDeltaRad = 0.03;
    static constexpr double kPhysicalLargeLeanMaxJointDeltaRad = 0.13;
    static constexpr double kMaxTargetSpeedRadS = 0.10;

    explicit SupportedBodyShiftPlan(
        GainStrategy strategy,
        RunMode run_mode=RunMode::FullSequence)
        : strategy_(strategy), run_mode_(run_mode) {
        const Eigen::Vector3d nominal_stand(
            0.0,-0.7729795255029084,1.5005003509817765);

        for(auto& q:stand_) q=nominal_stand;
        safe_scale_=FindMaximumSafeScale();
        safe_target_=SolveScale(safe_scale_);
        limiting_joint_=MaxDelta(safe_target_,&limiting_delta_);
        for(int level_index=0;level_index<3;++level_index) {
            scales_[level_index]=kSafeFractions[level_index]*safe_scale_;
            targets_[level_index]=SolveScale(scales_[level_index]);
        }
        reverse_y_target_=SolveTranslation(
            scales_[0]*kReferenceShiftXM,
            -scales_[0]*kReferenceShiftYM);
        refined_x_target_=SolveTranslation(kRefinedShiftXM,kRefinedShiftYM);
        zero_x_target_=SolveTranslation(kZeroXShiftXM,kZeroXShiftYM);
        y5_target_=SolveTranslation(kY5ShiftXM,kY5ShiftYM);
        y65_target_=SolveTranslation(kY65ShiftXM,kY65ShiftYM);
        x4y5_target_=SolveTranslation(kX4Y5ShiftXM,kX4Y5ShiftYM);
        x2y5_roll025_target_=SolvePose(
            kX2Y5Roll025ShiftXM,kX2Y5Roll025ShiftYM,kX2Y5Roll025Rad);
        x2y5_support05_target_=SolveSupportPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kX2Y5SupportExtensionM);
        x2y5_support075_target_=SolveSupportPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kX2Y5Support075ExtensionM);
        physical_candidate_targets_[0]=SolveSupportPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kPhysicalCandidate1ExtensionM);
        physical_candidate_targets_[1]=SolveSupportPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kPhysicalCandidate2ExtensionM);
        physical_candidate_targets_[2]=SolveSupportPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kPhysicalCandidate3ExtensionM);
        physical_pitch_n025_target_=SolveSupportPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kPhysicalCandidate1ExtensionM,kPhysicalPitchN025Rad);
        physical_pitch_p025_target_=SolveSupportPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kPhysicalCandidate1ExtensionM,kPhysicalPitchP025Rad);
        physical_height_p05_target_=SolveSupportPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kPhysicalHeightP05ExtensionM);
        physical_geometry_expand_target_=SolveGeometryPose(
            kX2Y5Support05ShiftXM,kX2Y5Support05ShiftYM,
            kPhysicalCandidate1ExtensionM,kPhysicalGeometryExpandOffsetM);
        for(int leg=0;leg<4;++leg)
            physical_force_opt1_target_[leg]=Eigen::Vector3d(
                kPhysicalForceOpt1Q[leg][0],kPhysicalForceOpt1Q[leg][1],
                kPhysicalForceOpt1Q[leg][2]);
        for(int leg=0;leg<4;++leg)
            physical_balanced_target_[leg]=Eigen::Vector3d(
                kPhysicalBalancedQ[leg][0],kPhysicalBalancedQ[leg][1],
                kPhysicalBalancedQ[leg][2]);
        for(int leg=0;leg<4;++leg)
            physical_force_opt2_target_[leg]=Eigen::Vector3d(
                kPhysicalForceOpt2Q[leg][0],kPhysicalForceOpt2Q[leg][1],
                kPhysicalForceOpt2Q[leg][2]);
        for(int leg=0;leg<4;++leg)
            physical_force_opt3_target_[leg]=Eigen::Vector3d(
                kPhysicalForceOpt3Q[leg][0],kPhysicalForceOpt3Q[leg][1],
                kPhysicalForceOpt3Q[leg][2]);
        for(int leg=0;leg<4;++leg)
            physical_large_lean_target_[leg]=Eigen::Vector3d(
                kPhysicalLargeLeanQ[leg][0],kPhysicalLargeLeanQ[leg][1],
                kPhysicalLargeLeanQ[leg][2]);
        BuildStagedSupportTrianglePlan();
    }

    Sample At(double seconds) const {
        const double t=std::max(0.0,seconds);
        if(t>=total_seconds()) {
            auto result=Hold(stand_,Phase::Complete,t);
            result.complete=true;
            return result;
        }
        if(run_mode_==RunMode::PhysicalStagedSupportTriangleOnly)
            return AtStagedSupportTriangle(t);

        const int level_index=run_mode_==RunMode::FullSequence
            ? std::min(2,static_cast<int>(t/kLevelSeconds))
            : SelectedLevelIndex();
        const double local=run_mode_==RunMode::FullSequence
            ? t-level_index*kLevelSeconds : t;
        const bool inverse_statics=run_mode_==RunMode::PhysicalForceOpt1Only ||
            run_mode_==RunMode::PhysicalBalancedOnly;
        const bool force_opt2=run_mode_==RunMode::PhysicalForceOpt2Only;
        const bool force_opt3=run_mode_==RunMode::PhysicalForceOpt3Only;
        const bool physical_large_lean=
            run_mode_==RunMode::PhysicalLargeLeanOnly;
        const bool conservative_force_opt=force_opt2 || force_opt3;
        const double shift_seconds=physical_large_lean
            ? kPhysicalLargeLeanShiftSeconds : conservative_force_opt
            ? kPhysicalForceOpt2ShiftSeconds : inverse_statics
            ? kPhysicalForceOptShiftSeconds : kShiftSeconds;
        const double recenter_seconds=physical_large_lean
            ? kPhysicalLargeLeanRecenterSeconds : conservative_force_opt
            ? kPhysicalForceOpt2RecenterSeconds : inverse_statics
            ? kPhysicalForceOptRecenterSeconds : kRecenterSeconds;
        const bool reverse_y=run_mode_==RunMode::Level30ReverseYOnly;
        const bool refined_x=run_mode_==RunMode::Level30RefinedXOnly;
        const bool zero_x=run_mode_==RunMode::Level30ZeroXOnly;
        const bool y5=run_mode_==RunMode::LevelY5Only;
        const bool y65=run_mode_==RunMode::LevelY65Only;
        const bool x4y5=run_mode_==RunMode::LevelX4Y5Only;
        const bool x2y5_roll025=
            run_mode_==RunMode::LevelX2Y5Roll025Only;
        const bool x2y5_support05=
            run_mode_==RunMode::LevelX2Y5Support05Only;
        const bool x2y5_support075=
            run_mode_==RunMode::LevelX2Y5Support075Only;
        const int physical_candidate=PhysicalCandidateIndex();
        const bool physical_pitch_n025=
            run_mode_==RunMode::PhysicalPitchN025Only;
        const bool physical_pitch_p025=
            run_mode_==RunMode::PhysicalPitchP025Only;
        const bool physical_height_p05=
            run_mode_==RunMode::PhysicalHeightP05Only;
        const bool physical_geometry_expand=
            run_mode_==RunMode::PhysicalGeometryExpandOnly;
        const bool physical_force_opt1=
            run_mode_==RunMode::PhysicalForceOpt1Only;
        const bool physical_balanced=
            run_mode_==RunMode::PhysicalBalancedOnly;
        const auto settle_phase=physical_candidate==0 ? Phase::SettlePhysicalCandidate1 :
            physical_candidate==1 ? Phase::SettlePhysicalCandidate2 :
            physical_candidate==2 ? Phase::SettlePhysicalCandidate3 :
            physical_pitch_n025 ? Phase::SettlePhysicalPitchN025 :
            physical_pitch_p025 ? Phase::SettlePhysicalPitchP025 :
            physical_height_p05 ? Phase::SettlePhysicalHeightP05 :
            physical_geometry_expand ? Phase::SettlePhysicalGeometryExpand :
            physical_large_lean ? Phase::SettlePhysicalLargeLean :
            force_opt3 ? Phase::SettlePhysicalForceOpt3 :
            force_opt2 ? Phase::SettlePhysicalForceOpt2 :
            physical_balanced ? Phase::SettlePhysicalBalanced :
            physical_force_opt1 ? Phase::SettlePhysicalForceOpt1 :
            x2y5_support075 ? Phase::SettleX2Y5Support075 :
            x2y5_support05 ? Phase::SettleX2Y5Support05 :
            x2y5_roll025 ? Phase::SettleX2Y5Roll025 :
            x4y5 ? Phase::SettleX4Y5 :
            y65 ? Phase::SettleY65 :
            y5 ? Phase::SettleY5 :
            zero_x ? Phase::Settle30ZeroX :
            refined_x ? Phase::Settle30RefinedX :
            reverse_y ? Phase::Settle30ReverseY :
            level_index==0 ? Phase::Settle30 :
            level_index==1 ? Phase::Settle60 : Phase::Settle90;
        const auto shift_phase=physical_candidate==0 ? Phase::ShiftPhysicalCandidate1 :
            physical_candidate==1 ? Phase::ShiftPhysicalCandidate2 :
            physical_candidate==2 ? Phase::ShiftPhysicalCandidate3 :
            physical_pitch_n025 ? Phase::ShiftPhysicalPitchN025 :
            physical_pitch_p025 ? Phase::ShiftPhysicalPitchP025 :
            physical_height_p05 ? Phase::ShiftPhysicalHeightP05 :
            physical_geometry_expand ? Phase::ShiftPhysicalGeometryExpand :
            physical_large_lean ? Phase::ShiftPhysicalLargeLean :
            force_opt3 ? Phase::ShiftPhysicalForceOpt3 :
            force_opt2 ? Phase::ShiftPhysicalForceOpt2 :
            physical_balanced ? Phase::ShiftPhysicalBalanced :
            physical_force_opt1 ? Phase::ShiftPhysicalForceOpt1 :
            x2y5_support075 ? Phase::ShiftX2Y5Support075 :
            x2y5_support05 ? Phase::ShiftX2Y5Support05 :
            x2y5_roll025 ? Phase::ShiftX2Y5Roll025 :
            x4y5 ? Phase::ShiftX4Y5 :
            y65 ? Phase::ShiftY65 :
            y5 ? Phase::ShiftY5 :
            zero_x ? Phase::Shift30ZeroX :
            refined_x ? Phase::Shift30RefinedX :
            reverse_y ? Phase::Shift30ReverseY :
            level_index==0 ? Phase::Shift30 :
            level_index==1 ? Phase::Shift60 : Phase::Shift90;
        const auto hold_phase=physical_candidate==0 ? Phase::HoldPhysicalCandidate1 :
            physical_candidate==1 ? Phase::HoldPhysicalCandidate2 :
            physical_candidate==2 ? Phase::HoldPhysicalCandidate3 :
            physical_pitch_n025 ? Phase::HoldPhysicalPitchN025 :
            physical_pitch_p025 ? Phase::HoldPhysicalPitchP025 :
            physical_height_p05 ? Phase::HoldPhysicalHeightP05 :
            physical_geometry_expand ? Phase::HoldPhysicalGeometryExpand :
            physical_large_lean ? Phase::HoldPhysicalLargeLean :
            force_opt3 ? Phase::HoldPhysicalForceOpt3 :
            force_opt2 ? Phase::HoldPhysicalForceOpt2 :
            physical_balanced ? Phase::HoldPhysicalBalanced :
            physical_force_opt1 ? Phase::HoldPhysicalForceOpt1 :
            x2y5_support075 ? Phase::HoldX2Y5Support075 :
            x2y5_support05 ? Phase::HoldX2Y5Support05 :
            x2y5_roll025 ? Phase::HoldX2Y5Roll025 :
            x4y5 ? Phase::HoldX4Y5 :
            y65 ? Phase::HoldY65 :
            y5 ? Phase::HoldY5 :
            zero_x ? Phase::Hold30ZeroX :
            refined_x ? Phase::Hold30RefinedX :
            reverse_y ? Phase::Hold30ReverseY :
            level_index==0 ? Phase::Hold30 :
            level_index==1 ? Phase::Hold60 : Phase::Hold90;
        const auto recenter_phase=physical_candidate==0 ? Phase::RecenterPhysicalCandidate1 :
            physical_candidate==1 ? Phase::RecenterPhysicalCandidate2 :
            physical_candidate==2 ? Phase::RecenterPhysicalCandidate3 :
            physical_pitch_n025 ? Phase::RecenterPhysicalPitchN025 :
            physical_pitch_p025 ? Phase::RecenterPhysicalPitchP025 :
            physical_height_p05 ? Phase::RecenterPhysicalHeightP05 :
            physical_geometry_expand ? Phase::RecenterPhysicalGeometryExpand :
            physical_large_lean ? Phase::RecenterPhysicalLargeLean :
            force_opt3 ? Phase::RecenterPhysicalForceOpt3 :
            force_opt2 ? Phase::RecenterPhysicalForceOpt2 :
            physical_balanced ? Phase::RecenterPhysicalBalanced :
            physical_force_opt1 ? Phase::RecenterPhysicalForceOpt1 :
            x2y5_support075 ? Phase::RecenterX2Y5Support075 :
            x2y5_support05 ? Phase::RecenterX2Y5Support05 :
            x2y5_roll025 ? Phase::RecenterX2Y5Roll025 :
            x4y5 ? Phase::RecenterX4Y5 :
            y65 ? Phase::RecenterY65 :
            y5 ? Phase::RecenterY5 :
            zero_x ? Phase::Recenter30ZeroX :
            refined_x ? Phase::Recenter30RefinedX :
            reverse_y ? Phase::Recenter30ReverseY :
            level_index==0 ? Phase::Recenter30 :
            level_index==1 ? Phase::Recenter60 : Phase::Recenter90;
        const auto& level_target=physical_candidate>=0
            ? physical_candidate_targets_[physical_candidate] :
            physical_pitch_n025 ? physical_pitch_n025_target_ :
            physical_pitch_p025 ? physical_pitch_p025_target_ :
            physical_height_p05 ? physical_height_p05_target_ :
            physical_geometry_expand ? physical_geometry_expand_target_ :
            physical_large_lean ? physical_large_lean_target_ :
            force_opt3 ? physical_force_opt3_target_ :
            force_opt2 ? physical_force_opt2_target_ :
            physical_balanced ? physical_balanced_target_ :
            physical_force_opt1 ? physical_force_opt1_target_ :
            x2y5_support075 ? x2y5_support075_target_ :
            x2y5_support05 ? x2y5_support05_target_ :
            x2y5_roll025 ? x2y5_roll025_target_ :
            x4y5 ? x4y5_target_ :
            y65 ? y65_target_ :
            y5 ? y5_target_ :
            zero_x ? zero_x_target_ :
            refined_x ? refined_x_target_ :
            reverse_y ? reverse_y_target_ : targets_[level_index];

        if(local<kSettleSeconds)
            return Hold(stand_,settle_phase,t);
        if(local<kSettleSeconds+shift_seconds)
            return Interpolate(
                stand_,level_target,
                (local-kSettleSeconds)/shift_seconds,
                shift_seconds,shift_phase,t);
        if(local<kSettleSeconds+shift_seconds+kHoldSeconds)
            return Hold(level_target,hold_phase,t);
        return Interpolate(
            level_target,stand_,
            (local-kSettleSeconds-shift_seconds-kHoldSeconds)/
                recenter_seconds,
            recenter_seconds,recenter_phase,t);
    }

    double total_seconds() const {
        if(run_mode_==RunMode::PhysicalStagedSupportTriangleOnly) {
            double total=0.0;
            for(const auto& waypoint:staged_waypoints_) total+=waypoint.duration;
            return total;
        }
        return run_mode_==RunMode::FullSequence ? kTotalSeconds :
            kSettleSeconds+
            (run_mode_==RunMode::PhysicalLargeLeanOnly
                ? kPhysicalLargeLeanShiftSeconds :
             (run_mode_==RunMode::PhysicalForceOpt2Only ||
              run_mode_==RunMode::PhysicalForceOpt3Only)
                ? kPhysicalForceOpt2ShiftSeconds :
             (run_mode_==RunMode::PhysicalForceOpt1Only ||
              run_mode_==RunMode::PhysicalBalancedOnly)
                ? kPhysicalForceOptShiftSeconds : kShiftSeconds)+
            kHoldSeconds+
            (run_mode_==RunMode::PhysicalLargeLeanOnly
                ? kPhysicalLargeLeanRecenterSeconds :
             (run_mode_==RunMode::PhysicalForceOpt2Only ||
              run_mode_==RunMode::PhysicalForceOpt3Only)
                ? kPhysicalForceOpt2RecenterSeconds :
             (run_mode_==RunMode::PhysicalForceOpt1Only ||
              run_mode_==RunMode::PhysicalBalancedOnly)
                ? kPhysicalForceOptRecenterSeconds : kRecenterSeconds);
    }

    const std::array<Eigen::Vector3d,4>& stand() const { return stand_; }
    double safe_scale() const { return safe_scale_; }
    double scale(int level_index) const {
        if(level_index<0 || level_index>=3)
            throw std::out_of_range("body-shift calibration level");
        return scales_[level_index];
    }
    const std::array<Eigen::Vector3d,4>& safe_target() const {
        return safe_target_;
    }
    int limiting_joint() const { return limiting_joint_; }
    double limiting_delta() const { return limiting_delta_; }
    const std::array<Eigen::Vector3d,4>& target(int level_index) const {
        if(level_index<0 || level_index>=3)
            throw std::out_of_range("body-shift calibration level");
        return targets_[level_index];
    }
    const std::array<Eigen::Vector3d,4>& reverse_y_target() const {
        return reverse_y_target_;
    }
    const std::array<Eigen::Vector3d,4>& refined_x_target() const {
        return refined_x_target_;
    }
    const std::array<Eigen::Vector3d,4>& zero_x_target() const {
        return zero_x_target_;
    }
    const std::array<Eigen::Vector3d,4>& y5_target() const {
        return y5_target_;
    }
    const std::array<Eigen::Vector3d,4>& y65_target() const {
        return y65_target_;
    }
    const std::array<Eigen::Vector3d,4>& x4y5_target() const {
        return x4y5_target_;
    }
    const std::array<Eigen::Vector3d,4>& x2y5_roll025_target() const {
        return x2y5_roll025_target_;
    }
    const std::array<Eigen::Vector3d,4>& x2y5_support05_target() const {
        return x2y5_support05_target_;
    }
    const std::array<Eigen::Vector3d,4>& x2y5_support075_target() const {
        return x2y5_support075_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_candidate_target(int index) const {
        if(index<0 || index>=3) throw std::out_of_range("physical candidate");
        return physical_candidate_targets_[index];
    }
    const std::array<Eigen::Vector3d,4>& physical_pitch_n025_target() const {
        return physical_pitch_n025_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_pitch_p025_target() const {
        return physical_pitch_p025_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_height_p05_target() const {
        return physical_height_p05_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_geometry_expand_target() const {
        return physical_geometry_expand_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_force_opt1_target() const {
        return physical_force_opt1_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_balanced_target() const {
        return physical_balanced_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_force_opt2_target() const {
        return physical_force_opt2_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_force_opt3_target() const {
        return physical_force_opt3_target_;
    }
    const std::array<Eigen::Vector3d,4>& physical_large_lean_target() const {
        return physical_large_lean_target_;
    }
    double max_joint_delta_rad() const {
        return (run_mode_==RunMode::PhysicalLargeLeanOnly ||
                run_mode_==RunMode::PhysicalStagedSupportTriangleOnly)
            ? kPhysicalLargeLeanMaxJointDeltaRad : kMaxJointDeltaRad;
    }
    const std::array<Eigen::Vector3d,4>& staged_final_target() const {
        return staged_final_target_;
    }

    static const char* PhaseName(Phase phase) {
        switch(phase) {
            case Phase::Settle30: return "BODY_SHIFT_SAFE_30_SETTLE";
            case Phase::Shift30: return "BODY_SHIFT_SAFE_30_MOVING";
            case Phase::Hold30: return "BODY_SHIFT_SAFE_30_HOLD";
            case Phase::Recenter30: return "BODY_SHIFT_SAFE_30_RECENTER";
            case Phase::Settle60: return "BODY_SHIFT_SAFE_60_SETTLE";
            case Phase::Shift60: return "BODY_SHIFT_SAFE_60_MOVING";
            case Phase::Hold60: return "BODY_SHIFT_SAFE_60_HOLD";
            case Phase::Recenter60: return "BODY_SHIFT_SAFE_60_RECENTER";
            case Phase::Settle90: return "BODY_SHIFT_SAFE_90_SETTLE";
            case Phase::Shift90: return "BODY_SHIFT_SAFE_90_MOVING";
            case Phase::Hold90: return "BODY_SHIFT_SAFE_90_HOLD";
            case Phase::Recenter90: return "BODY_SHIFT_SAFE_90_RECENTER";
            case Phase::Settle30ReverseY: return "BODY_SHIFT_SAFE_30_REVERSE_Y_SETTLE";
            case Phase::Shift30ReverseY: return "BODY_SHIFT_SAFE_30_REVERSE_Y_MOVING";
            case Phase::Hold30ReverseY: return "BODY_SHIFT_SAFE_30_REVERSE_Y_HOLD";
            case Phase::Recenter30ReverseY: return "BODY_SHIFT_SAFE_30_REVERSE_Y_RECENTER";
            case Phase::Settle30RefinedX: return "BODY_SHIFT_SAFE_30_REFINED_X_SETTLE";
            case Phase::Shift30RefinedX: return "BODY_SHIFT_SAFE_30_REFINED_X_MOVING";
            case Phase::Hold30RefinedX: return "BODY_SHIFT_SAFE_30_REFINED_X_HOLD";
            case Phase::Recenter30RefinedX: return "BODY_SHIFT_SAFE_30_REFINED_X_RECENTER";
            case Phase::Settle30ZeroX: return "BODY_SHIFT_SAFE_30_ZERO_X_SETTLE";
            case Phase::Shift30ZeroX: return "BODY_SHIFT_SAFE_30_ZERO_X_MOVING";
            case Phase::Hold30ZeroX: return "BODY_SHIFT_SAFE_30_ZERO_X_HOLD";
            case Phase::Recenter30ZeroX: return "BODY_SHIFT_SAFE_30_ZERO_X_RECENTER";
            case Phase::SettleY5: return "BODY_SHIFT_Y5_SETTLE";
            case Phase::ShiftY5: return "BODY_SHIFT_Y5_MOVING";
            case Phase::HoldY5: return "BODY_SHIFT_Y5_HOLD";
            case Phase::RecenterY5: return "BODY_SHIFT_Y5_RECENTER";
            case Phase::SettleY65: return "BODY_SHIFT_Y65_SETTLE";
            case Phase::ShiftY65: return "BODY_SHIFT_Y65_MOVING";
            case Phase::HoldY65: return "BODY_SHIFT_Y65_HOLD";
            case Phase::RecenterY65: return "BODY_SHIFT_Y65_RECENTER";
            case Phase::SettleX4Y5: return "BODY_SHIFT_X4_Y5_SETTLE";
            case Phase::ShiftX4Y5: return "BODY_SHIFT_X4_Y5_MOVING";
            case Phase::HoldX4Y5: return "BODY_SHIFT_X4_Y5_HOLD";
            case Phase::RecenterX4Y5: return "BODY_SHIFT_X4_Y5_RECENTER";
            case Phase::SettleX2Y5Roll025: return "BODY_SHIFT_X2_Y5_ROLL025_SETTLE";
            case Phase::ShiftX2Y5Roll025: return "BODY_SHIFT_X2_Y5_ROLL025_MOVING";
            case Phase::HoldX2Y5Roll025: return "BODY_SHIFT_X2_Y5_ROLL025_HOLD";
            case Phase::RecenterX2Y5Roll025: return "BODY_SHIFT_X2_Y5_ROLL025_RECENTER";
            case Phase::SettleX2Y5Support05: return "BODY_SHIFT_X2_Y5_SUPPORT05_SETTLE";
            case Phase::ShiftX2Y5Support05: return "BODY_SHIFT_X2_Y5_SUPPORT05_MOVING";
            case Phase::HoldX2Y5Support05: return "BODY_SHIFT_X2_Y5_SUPPORT05_HOLD";
            case Phase::RecenterX2Y5Support05: return "BODY_SHIFT_X2_Y5_SUPPORT05_RECENTER";
            case Phase::SettleX2Y5Support075: return "BODY_SHIFT_X2_Y5_SUPPORT075_SETTLE";
            case Phase::ShiftX2Y5Support075: return "BODY_SHIFT_X2_Y5_SUPPORT075_MOVING";
            case Phase::HoldX2Y5Support075: return "BODY_SHIFT_X2_Y5_SUPPORT075_HOLD";
            case Phase::RecenterX2Y5Support075: return "BODY_SHIFT_X2_Y5_SUPPORT075_RECENTER";
            case Phase::SettlePhysicalCandidate1: return "BODY_SHIFT_PHYS_C1_SETTLE";
            case Phase::ShiftPhysicalCandidate1: return "BODY_SHIFT_PHYS_C1_MOVING";
            case Phase::HoldPhysicalCandidate1: return "BODY_SHIFT_PHYS_C1_HOLD";
            case Phase::RecenterPhysicalCandidate1: return "BODY_SHIFT_PHYS_C1_RECENTER";
            case Phase::SettlePhysicalCandidate2: return "BODY_SHIFT_PHYS_C2_SETTLE";
            case Phase::ShiftPhysicalCandidate2: return "BODY_SHIFT_PHYS_C2_MOVING";
            case Phase::HoldPhysicalCandidate2: return "BODY_SHIFT_PHYS_C2_HOLD";
            case Phase::RecenterPhysicalCandidate2: return "BODY_SHIFT_PHYS_C2_RECENTER";
            case Phase::SettlePhysicalCandidate3: return "BODY_SHIFT_PHYS_C3_SETTLE";
            case Phase::ShiftPhysicalCandidate3: return "BODY_SHIFT_PHYS_C3_MOVING";
            case Phase::HoldPhysicalCandidate3: return "BODY_SHIFT_PHYS_C3_HOLD";
            case Phase::RecenterPhysicalCandidate3: return "BODY_SHIFT_PHYS_C3_RECENTER";
            case Phase::SettlePhysicalPitchN025: return "BODY_SHIFT_PHYS_PITCH_N025_SETTLE";
            case Phase::ShiftPhysicalPitchN025: return "BODY_SHIFT_PHYS_PITCH_N025_MOVING";
            case Phase::HoldPhysicalPitchN025: return "BODY_SHIFT_PHYS_PITCH_N025_HOLD";
            case Phase::RecenterPhysicalPitchN025: return "BODY_SHIFT_PHYS_PITCH_N025_RECENTER";
            case Phase::SettlePhysicalPitchP025: return "BODY_SHIFT_PHYS_PITCH_P025_SETTLE";
            case Phase::ShiftPhysicalPitchP025: return "BODY_SHIFT_PHYS_PITCH_P025_MOVING";
            case Phase::HoldPhysicalPitchP025: return "BODY_SHIFT_PHYS_PITCH_P025_HOLD";
            case Phase::RecenterPhysicalPitchP025: return "BODY_SHIFT_PHYS_PITCH_P025_RECENTER";
            case Phase::SettlePhysicalHeightP05: return "BODY_SHIFT_PHYS_HEIGHT_P05_SETTLE";
            case Phase::ShiftPhysicalHeightP05: return "BODY_SHIFT_PHYS_HEIGHT_P05_MOVING";
            case Phase::HoldPhysicalHeightP05: return "BODY_SHIFT_PHYS_HEIGHT_P05_HOLD";
            case Phase::RecenterPhysicalHeightP05: return "BODY_SHIFT_PHYS_HEIGHT_P05_RECENTER";
            case Phase::SettlePhysicalGeometryExpand: return "BODY_SHIFT_PHYS_GEOM_EXPAND_SETTLE";
            case Phase::ShiftPhysicalGeometryExpand: return "BODY_SHIFT_PHYS_GEOM_EXPAND_MOVING";
            case Phase::HoldPhysicalGeometryExpand: return "BODY_SHIFT_PHYS_GEOM_EXPAND_HOLD";
            case Phase::RecenterPhysicalGeometryExpand: return "BODY_SHIFT_PHYS_GEOM_EXPAND_RECENTER";
            case Phase::SettlePhysicalForceOpt1: return "BODY_SHIFT_PHYS_FORCE_OPT1_SETTLE";
            case Phase::ShiftPhysicalForceOpt1: return "BODY_SHIFT_PHYS_FORCE_OPT1_MOVING";
            case Phase::HoldPhysicalForceOpt1: return "BODY_SHIFT_PHYS_FORCE_OPT1_HOLD";
            case Phase::RecenterPhysicalForceOpt1: return "BODY_SHIFT_PHYS_FORCE_OPT1_RECENTER";
            case Phase::SettlePhysicalBalanced: return "BODY_SHIFT_PHYS_BALANCED_SETTLE";
            case Phase::ShiftPhysicalBalanced: return "BODY_SHIFT_PHYS_BALANCED_MOVING";
            case Phase::HoldPhysicalBalanced: return "BODY_SHIFT_PHYS_BALANCED_HOLD";
            case Phase::RecenterPhysicalBalanced: return "BODY_SHIFT_PHYS_BALANCED_RECENTER";
            case Phase::SettlePhysicalForceOpt2: return "BODY_SHIFT_PHYS_FORCE_OPT2_SETTLE";
            case Phase::ShiftPhysicalForceOpt2: return "BODY_SHIFT_PHYS_FORCE_OPT2_MOVING";
            case Phase::HoldPhysicalForceOpt2: return "BODY_SHIFT_PHYS_FORCE_OPT2_HOLD";
            case Phase::RecenterPhysicalForceOpt2: return "BODY_SHIFT_PHYS_FORCE_OPT2_RECENTER";
            case Phase::SettlePhysicalForceOpt3: return "BODY_SHIFT_PHYS_FORCE_OPT3_SETTLE";
            case Phase::ShiftPhysicalForceOpt3: return "BODY_SHIFT_PHYS_FORCE_OPT3_MOVING";
            case Phase::HoldPhysicalForceOpt3: return "BODY_SHIFT_PHYS_FORCE_OPT3_HOLD";
            case Phase::RecenterPhysicalForceOpt3: return "BODY_SHIFT_PHYS_FORCE_OPT3_RECENTER";
            case Phase::SettlePhysicalLargeLean: return "BODY_SHIFT_PHYS_LARGE_LEAN_SETTLE";
            case Phase::ShiftPhysicalLargeLean: return "BODY_SHIFT_PHYS_LARGE_LEAN_MOVING";
            case Phase::HoldPhysicalLargeLean: return "BODY_SHIFT_PHYS_LARGE_LEAN_HOLD";
            case Phase::RecenterPhysicalLargeLean: return "BODY_SHIFT_PHYS_LARGE_LEAN_RECENTER";
            case Phase::StagedSettle: return "STANCE_STAGE_SETTLE";
            case Phase::StagedFLUnload: return "STANCE_STAGE_FL_UNLOAD";
            case Phase::StagedFLLift: return "STANCE_STAGE_FL_LIFT";
            case Phase::StagedFLMove: return "STANCE_STAGE_FL_MOVE";
            case Phase::StagedFLLower: return "STANCE_STAGE_FL_LOWER";
            case Phase::StagedFLSettle: return "STANCE_STAGE_FL_SETTLE";
            case Phase::StagedHLUnload: return "STANCE_STAGE_HL_UNLOAD";
            case Phase::StagedHLLift: return "STANCE_STAGE_HL_LIFT";
            case Phase::StagedHLMove: return "STANCE_STAGE_HL_MOVE";
            case Phase::StagedHLLower: return "STANCE_STAGE_HL_LOWER";
            case Phase::StagedHLSettle: return "STANCE_STAGE_HL_SETTLE";
            case Phase::StagedHRUnload: return "STANCE_STAGE_HR_UNLOAD";
            case Phase::StagedHRLift: return "STANCE_STAGE_HR_LIFT";
            case Phase::StagedHRMove: return "STANCE_STAGE_HR_MOVE";
            case Phase::StagedHRLower: return "STANCE_STAGE_HR_LOWER";
            case Phase::StagedHRSettle: return "STANCE_STAGE_HR_SETTLE";
            case Phase::StagedFinalShift: return "STANCE_STAGE_FINAL_SHIFT";
            case Phase::StagedFinalHold: return "STANCE_STAGE_FINAL_HOLD";
            case Phase::StagedBodyRecenter: return "STANCE_STAGE_BODY_RECENTER";
            case Phase::StagedRestoreHRUnload: return "STANCE_RESTORE_HR_UNLOAD";
            case Phase::StagedRestoreHRLift: return "STANCE_RESTORE_HR_LIFT";
            case Phase::StagedRestoreHRMove: return "STANCE_RESTORE_HR_MOVE";
            case Phase::StagedRestoreHRLower: return "STANCE_RESTORE_HR_LOWER";
            case Phase::StagedRestoreHRSettle: return "STANCE_RESTORE_HR_SETTLE";
            case Phase::StagedRestoreHLUnload: return "STANCE_RESTORE_HL_UNLOAD";
            case Phase::StagedRestoreHLLift: return "STANCE_RESTORE_HL_LIFT";
            case Phase::StagedRestoreHLMove: return "STANCE_RESTORE_HL_MOVE";
            case Phase::StagedRestoreHLLower: return "STANCE_RESTORE_HL_LOWER";
            case Phase::StagedRestoreHLSettle: return "STANCE_RESTORE_HL_SETTLE";
            case Phase::StagedRestoreFLUnload: return "STANCE_RESTORE_FL_UNLOAD";
            case Phase::StagedRestoreFLLift: return "STANCE_RESTORE_FL_LIFT";
            case Phase::StagedRestoreFLMove: return "STANCE_RESTORE_FL_MOVE";
            case Phase::StagedRestoreFLLower: return "STANCE_RESTORE_FL_LOWER";
            case Phase::StagedRestoreFLSettle: return "STANCE_RESTORE_FL_SETTLE";
            case Phase::StagedFinalStand: return "STANCE_STAGE_FINAL_STAND";
            case Phase::Complete: return "BODY_SHIFT_VERIFY_STAND";
        }
        return "BODY_SHIFT_INVALID";
    }

private:
    using Pose=std::array<Eigen::Vector3d,4>;
    GainStrategy strategy_;
    RunMode run_mode_;
    Pose stand_{};
    Pose safe_target_{};
    Pose reverse_y_target_{};
    Pose refined_x_target_{};
    Pose zero_x_target_{};
    Pose y5_target_{};
    Pose y65_target_{};
    Pose x4y5_target_{};
    Pose x2y5_roll025_target_{};
    Pose x2y5_support05_target_{};
    Pose x2y5_support075_target_{};
    std::array<Pose,3> physical_candidate_targets_{};
    Pose physical_pitch_n025_target_{};
    Pose physical_pitch_p025_target_{};
    Pose physical_height_p05_target_{};
    Pose physical_geometry_expand_target_{};
    Pose physical_force_opt1_target_{};
    Pose physical_balanced_target_{};
    Pose physical_force_opt2_target_{};
    Pose physical_force_opt3_target_{};
    Pose physical_large_lean_target_{};
    Pose staged_final_target_{};
    struct StagedWaypoint { Pose target{}; double duration=0.0; Phase phase=Phase::StagedSettle; };
    std::vector<StagedWaypoint> staged_waypoints_;
    std::array<Pose,3> targets_{};
    std::array<double,3> scales_{};
    double safe_scale_{0.0};
    int limiting_joint_{-1};
    double limiting_delta_{0.0};

    int SelectedLevelIndex() const {
        switch(run_mode_) {
            case RunMode::Level30Only: return 0;
            case RunMode::Level60Only: return 1;
            case RunMode::Level90Only: return 2;
            case RunMode::Level30ReverseYOnly: return 0;
            case RunMode::Level30RefinedXOnly: return 0;
            case RunMode::Level30ZeroXOnly: return 0;
            case RunMode::LevelY5Only: return 0;
            case RunMode::LevelY65Only: return 0;
            case RunMode::LevelX4Y5Only: return 0;
            case RunMode::LevelX2Y5Roll025Only: return 0;
            case RunMode::LevelX2Y5Support05Only: return 0;
            case RunMode::LevelX2Y5Support075Only: return 0;
            case RunMode::PhysicalCandidate1Only: return 0;
            case RunMode::PhysicalCandidate2Only: return 0;
            case RunMode::PhysicalCandidate3Only: return 0;
            case RunMode::PhysicalPitchN025Only: return 0;
            case RunMode::PhysicalPitchP025Only: return 0;
            case RunMode::PhysicalHeightP05Only: return 0;
            case RunMode::PhysicalGeometryExpandOnly: return 0;
            case RunMode::PhysicalForceOpt1Only: return 0;
            case RunMode::PhysicalBalancedOnly: return 0;
            case RunMode::PhysicalForceOpt2Only: return 0;
            case RunMode::PhysicalForceOpt3Only: return 0;
            case RunMode::PhysicalLargeLeanOnly: return 0;
            case RunMode::PhysicalStagedSupportTriangleOnly: return 0;
            case RunMode::FullSequence: return 0;
        }
        return 0;
    }

    int PhysicalCandidateIndex() const {
        switch(run_mode_) {
            case RunMode::PhysicalCandidate1Only: return 0;
            case RunMode::PhysicalCandidate2Only: return 1;
            case RunMode::PhysicalCandidate3Only: return 2;
            default: return -1;
        }
    }

    Pose SolveScale(double scale) const {
        return SolveTranslation(
            scale*kReferenceShiftXM,
            scale*kReferenceShiftYM);
    }

    Pose SolveTranslation(double x,double y) const {
        return SolvePose(x,y,0.0);
    }

    Pose SolvePose(double x,double y,double roll) const {
        Pose pose{};
        const Eigen::Matrix3d rotation=Eigen::AngleAxisd(
            roll,Eigen::Vector3d::UnitX()).toRotationMatrix();
        for(int leg_index=0;leg_index<4;++leg_index) {
            const auto leg=static_cast<lite3::Leg>(leg_index);
            const auto nominal_foot=lite3::FootPositionBody(
                leg,stand_[leg_index]);
            const Eigen::Vector3d body_translation(
                x,y,0.0);
            const auto solved=lite3::SolveFootIk(
                leg,rotation.transpose()*(nominal_foot-body_translation),
                stand_[leg_index]);
            if(!solved.converged || solved.residual_m>5e-6)
                throw std::runtime_error("body-shift calibration IK failed");
            pose[leg_index]=solved.q;
        }
        return pose;
    }

    Pose SolveSupportPose(double x,double y,
                          const std::array<double,4>& extension,
                          double pitch=0.0) const {
        Pose pose{};
        const Eigen::Matrix3d rotation=Eigen::AngleAxisd(
            pitch,Eigen::Vector3d::UnitY()).toRotationMatrix();
        for(int leg_index=0;leg_index<4;++leg_index) {
            const auto leg=static_cast<lite3::Leg>(leg_index);
            const auto nominal_foot=lite3::FootPositionBody(
                leg,stand_[leg_index]);
            Eigen::Vector3d target=rotation.transpose()*
                (nominal_foot-Eigen::Vector3d(x,y,0.0));
            target.z()-=extension[leg_index];
            const auto solved=lite3::SolveFootIk(
                leg,target,stand_[leg_index]);
            if(!solved.converged || solved.residual_m>5e-6)
                throw std::runtime_error("body-shift support-posture IK failed");
            pose[leg_index]=solved.q;
        }
        return pose;
    }

    Pose SolveGeometryPose(
        double x,double y,const std::array<double,4>& extension,
        const std::array<std::array<double,3>,4>& offsets) const {
        Pose pose{};
        for(int leg_index=0;leg_index<4;++leg_index) {
            const auto leg=static_cast<lite3::Leg>(leg_index);
            const auto nominal_foot=lite3::FootPositionBody(
                leg,stand_[leg_index]);
            Eigen::Vector3d target=
                nominal_foot-Eigen::Vector3d(x,y,0.0)+Eigen::Vector3d(
                    offsets[leg_index][0],offsets[leg_index][1],
                    offsets[leg_index][2]);
            target.z()-=extension[leg_index];
            const auto solved=lite3::SolveFootIk(
                leg,target,stand_[leg_index]);
            if(!solved.converged || solved.residual_m>5e-6)
                throw std::runtime_error("support-geometry IK failed");
            pose[leg_index]=solved.q;
        }
        return pose;
    }

    using StagedOffsets=std::array<std::array<double,3>,4>;

    Pose SolveStagedPose(const Eigen::Vector3d& body,
                         const StagedOffsets& offsets,
                         int lifted_leg=-1,double lift_m=0.0) const {
        Pose pose{};
        for(int leg_index=0;leg_index<4;++leg_index) {
            const auto leg=static_cast<lite3::Leg>(leg_index);
            Eigen::Vector3d target=lite3::FootPositionBody(
                leg,stand_[leg_index])+Eigen::Vector3d(
                    offsets[leg_index][0],offsets[leg_index][1],
                    offsets[leg_index][2])-body;
            if(leg_index==lifted_leg) target.z()+=lift_m;
            const auto solved=lite3::SolveFootIk(
                leg,target,stand_[leg_index]);
            if(!solved.converged || solved.residual_m>5e-6)
                throw std::runtime_error("staged support-foot IK failed");
            pose[leg_index]=solved.q;
        }
        return pose;
    }

    void AddStagedWaypoint(const Pose& target,double duration,Phase phase) {
        staged_waypoints_.push_back({target,duration,phase});
    }

    void BuildStagedSupportTrianglePlan() {
        StagedOffsets offsets{};
        const StagedOffsets final_offsets{{
            {{ 0.0140, 0.0140,0.0}},
            {{ 0.0,    0.0,   0.0}},
            {{-0.0140, 0.0140,0.0}},
            {{-0.0070,-0.0175,0.0}}}};
        const std::array<Eigen::Vector3d,4> unload_body{{
            Eigen::Vector3d(-0.010,-0.010,0.0),
            Eigen::Vector3d::Zero(),
            Eigen::Vector3d( 0.010,-0.010,0.0),
            Eigen::Vector3d( 0.010, 0.010,0.0)}};
        const std::array<int,3> place_order{{0,2,3}};
        const std::array<Phase,3> unload_phase{{
            Phase::StagedFLUnload,Phase::StagedHLUnload,Phase::StagedHRUnload}};
        const std::array<Phase,3> lift_phase{{
            Phase::StagedFLLift,Phase::StagedHLLift,Phase::StagedHRLift}};
        const std::array<Phase,3> move_phase{{
            Phase::StagedFLMove,Phase::StagedHLMove,Phase::StagedHRMove}};
        const std::array<Phase,3> lower_phase{{
            Phase::StagedFLLower,Phase::StagedHLLower,Phase::StagedHRLower}};
        const std::array<Phase,3> settle_phase{{
            Phase::StagedFLSettle,Phase::StagedHLSettle,Phase::StagedHRSettle}};

        AddStagedWaypoint(stand_,kStagedSettleSeconds,Phase::StagedSettle);
        for(int index=0;index<3;++index) {
            const int leg=place_order[index];
            const auto body=unload_body[leg];
            AddStagedWaypoint(SolveStagedPose(body,offsets),
                              index==1 ? kStagedHLUnloadSeconds
                                       : kStagedUnloadSeconds,
                              unload_phase[index]);
            AddStagedWaypoint(SolveStagedPose(
                                  body,offsets,leg,kStagedFootClearanceM),
                              kStagedLiftSeconds,lift_phase[index]);
            offsets[leg]=final_offsets[leg];
            AddStagedWaypoint(SolveStagedPose(
                                  body,offsets,leg,kStagedFootClearanceM),
                              kStagedMoveSeconds,move_phase[index]);
            const auto lower=SolveStagedPose(body,offsets);
            AddStagedWaypoint(lower,kStagedLowerSeconds,lower_phase[index]);
            AddStagedWaypoint(lower,kStagedSettleSeconds,settle_phase[index]);
        }

        const Eigen::Vector3d mid_body(-0.007,0.0,0.0);
        const Eigen::Vector3d final_body(-0.014,0.0,0.0);
        const auto staged_mid_target=SolveStagedPose(mid_body,offsets);
        staged_final_target_=SolveStagedPose(final_body,offsets);
        AddStagedWaypoint(staged_final_target_,kStagedBodyShiftSeconds,
                          Phase::StagedFinalShift);
        AddStagedWaypoint(staged_final_target_,kHoldSeconds,
                          Phase::StagedFinalHold);
        AddStagedWaypoint(staged_mid_target,kStagedRecenterHalfSeconds,
                          Phase::StagedBodyRecenter);
        AddStagedWaypoint(staged_mid_target,kStagedMidShiftSettleSeconds,
                          Phase::StagedBodyRecenter);
        AddStagedWaypoint(SolveStagedPose(Eigen::Vector3d::Zero(),offsets),
                          kStagedRecenterHalfSeconds,
                          Phase::StagedBodyRecenter);

        const std::array<int,3> restore_order{{3,2,0}};
        const std::array<Phase,3> restore_unload{{
            Phase::StagedRestoreHRUnload,Phase::StagedRestoreHLUnload,
            Phase::StagedRestoreFLUnload}};
        const std::array<Phase,3> restore_lift{{
            Phase::StagedRestoreHRLift,Phase::StagedRestoreHLLift,
            Phase::StagedRestoreFLLift}};
        const std::array<Phase,3> restore_move{{
            Phase::StagedRestoreHRMove,Phase::StagedRestoreHLMove,
            Phase::StagedRestoreFLMove}};
        const std::array<Phase,3> restore_lower{{
            Phase::StagedRestoreHRLower,Phase::StagedRestoreHLLower,
            Phase::StagedRestoreFLLower}};
        const std::array<Phase,3> restore_settle{{
            Phase::StagedRestoreHRSettle,Phase::StagedRestoreHLSettle,
            Phase::StagedRestoreFLSettle}};
        for(int index=0;index<3;++index) {
            const int leg=restore_order[index];
            const auto body=unload_body[leg];
            AddStagedWaypoint(SolveStagedPose(body,offsets),
                              kStagedUnloadSeconds,restore_unload[index]);
            AddStagedWaypoint(SolveStagedPose(
                                  body,offsets,leg,kStagedFootClearanceM),
                              kStagedLiftSeconds,restore_lift[index]);
            offsets[leg]={{0.0,0.0,0.0}};
            AddStagedWaypoint(SolveStagedPose(
                                  body,offsets,leg,kStagedFootClearanceM),
                              kStagedMoveSeconds,restore_move[index]);
            const auto lower=SolveStagedPose(body,offsets);
            AddStagedWaypoint(lower,kStagedLowerSeconds,restore_lower[index]);
            AddStagedWaypoint(lower,kStagedSettleSeconds,
                              restore_settle[index]);
        }
        AddStagedWaypoint(stand_,kStagedFinalStandSeconds,
                          Phase::StagedFinalStand);
    }

    Sample AtStagedSupportTriangle(double seconds) const {
        double start=0.0;
        Pose previous=stand_;
        for(const auto& waypoint:staged_waypoints_) {
            const double end=start+waypoint.duration;
            if(seconds<end) {
                const double largest=[&] {
                    double result=0.0;
                    for(int leg=0;leg<4;++leg)
                        result=std::max(result,
                            (waypoint.target[leg]-previous[leg]).
                                cwiseAbs().maxCoeff());
                    return result;
                }();
                if(largest<1e-12)
                    return Hold(waypoint.target,waypoint.phase,seconds);
                return Interpolate(previous,waypoint.target,
                    (seconds-start)/waypoint.duration,waypoint.duration,
                    waypoint.phase,seconds);
            }
            previous=waypoint.target;
            start=end;
        }
        auto result=Hold(stand_,Phase::Complete,seconds);
        result.complete=true;
        return result;
    }

    int MaxDelta(const Pose& pose,double* value) const {
        int limiting=-1;
        double maximum=-1.0;
        for(int leg=0;leg<4;++leg) {
            for(int joint=0;joint<3;++joint) {
                const double delta=std::abs(
                    pose[leg][joint]-stand_[leg][joint]);
                if(delta>maximum) {
                    maximum=delta;
                    limiting=3*leg+joint;
                }
            }
        }
        if(value) *value=maximum;
        return limiting;
    }

    double FindMaximumSafeScale() const {
        double low=0.0,high=1.0;
        for(int iteration=0;iteration<80;++iteration) {
            const double candidate=0.5*(low+high);
            const auto pose=SolveScale(candidate);
            double maximum=0.0;
            MaxDelta(pose,&maximum);
            if(maximum<=kMaxJointDeltaRad)
                low=candidate;
            else
                high=candidate;
        }
        return low;
    }

    static double QuinticDerivative(double p) {
        const double s=std::clamp(p,0.0,1.0);
        return 30.0*s*s*(1.0-s)*(1.0-s);
    }

    std::pair<float,float> Gains(double elapsed) const {
        if(strategy_==GainStrategy::KeepStand)
            return {kStandKp,kStandKd};
        if(strategy_==GainStrategy::AbruptReduced)
            return {kReducedKp,kReducedKd};
        const double a=lite3::Quintic(std::clamp(
            elapsed/kGainRampSeconds,0.0,1.0));
        return {
            static_cast<float>(kStandKp+a*(kReducedKp-kStandKp)),
            static_cast<float>(kStandKd+a*(kReducedKd-kStandKd))};
    }

    Sample Interpolate(const Pose& from,const Pose& to,double p,
                       double duration,Phase phase,double elapsed) const {
        const double blend=lite3::Quintic(p);
        const double rate=QuinticDerivative(p)/duration;
        const auto [kp,kd]=Gains(elapsed);
        Sample out;
        out.phase=phase;
        for(int leg=0;leg<4;++leg) {
            for(int joint=0;joint<3;++joint) {
                const int i=3*leg+joint;
                const double delta=to[leg][joint]-from[leg][joint];
                out.command(i,0)=kp;
                out.command(i,1)=static_cast<float>(
                    from[leg][joint]+blend*delta);
                out.command(i,2)=kd;
                out.command(i,3)=static_cast<float>(rate*delta);
                out.command(i,4)=0.0f;
            }
        }
        return out;
    }

    Sample Hold(const Pose& pose,Phase phase,double elapsed) const {
        return Interpolate(pose,pose,0.0,1.0,phase,elapsed);
    }
};
