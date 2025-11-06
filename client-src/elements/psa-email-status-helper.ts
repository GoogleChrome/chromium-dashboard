// Copyright 2024 Google Inc. All rights reserved.
// Use of this source code is governed by the Apache License 2.0 that can be
// found in the LICENSE file.

/**
 * Helper module for checking PSA (Public Service Announcement) email status
 */

export interface Stage {
  stage_type?: string;
  stage_title?: string;
  type?: string;
  intent_thread_url?: string;
}

export interface Feature {
  stages?: Stage[];
  name?: string;
  id?: number;
}

/**
 * Checks if a given stage is a PSA type stage
 * @param stage - The stage object to check
 * @returns true if the stage is a PSA type
 */
export function isPSAStage(stage: Stage | undefined): boolean {
  if (!stage) return false;

  return (
    stage.stage_type === 'PSA' ||
    stage.stage_title === 'PSA' ||
    stage.type === 'PSA'
  );
}

/**
 * Checks if a PSA stage has a pending email notification
 * PSA email is pending if intent_thread_url is not populated
 * @param stage - The PSA stage to check
 * @returns true if PSA email is pending (not sent)
 */
export function isPSAEmailPending(stage: Stage | undefined): boolean {
  if (!stage) return false;

  if (!isPSAStage(stage)) return false;

  // Email is pending if intent_thread_url is empty, null, or undefined
  const hasIntentThread =
    stage.intent_thread_url && stage.intent_thread_url.trim() !== '';
  return !hasIntentThread;
}

/**
 * Gets the first pending PSA stage from a feature's stages
 * @param feature - The feature object containing stages
 * @returns The pending PSA stage or undefined if none found
 */
export function getPendingPSAStage(
  feature: Feature | undefined
): Stage | undefined {
  if (!feature || !feature.stages || feature.stages.length === 0) {
    return undefined;
  }

  return feature.stages.find((stage: Stage) => {
    return isPSAStage(stage) && isPSAEmailPending(stage);
  });
}

/**
 * Checks if a feature has any pending PSA emails
 * @param feature - The feature object to check
 * @returns true if the feature has at least one pending PSA email
 */
export function hasPendingPSAEmail(feature: Feature | undefined): boolean {
  return getPendingPSAStage(feature) !== undefined;
}

/**
 * Gets all pending PSA stages from a feature
 * @param feature - The feature object containing stages
 * @returns Array of pending PSA stages
 */
export function getAllPendingPSAStages(feature: Feature | undefined): Stage[] {
  if (!feature || !feature.stages || feature.stages.length === 0) {
    return [];
  }

  return feature.stages.filter((stage: Stage) => {
    return isPSAStage(stage) && isPSAEmailPending(stage);
  });
}
