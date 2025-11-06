// Copyright 2024 Google Inc. All rights reserved.
// Use of this source code is governed by the Apache License 2.0 that can be
// found in the LICENSE file.

import {assert} from '@esm-bundle/chai';
import {
  isPSAStage,
  isPSAEmailPending,
  getPendingPSAStage,
  hasPendingPSAEmail,
  getAllPendingPSAStages,
  Stage,
  Feature,
} from './psa-email-status-helper';

describe('PSA Email Status Helper Tests', () => {
  describe('isPSAStage', () => {
    it('should identify PSA stage by stage_type', () => {
      const stage: Stage = {
        stage_type: 'PSA',
        stage_title: 'Public Service Announcement',
      };
      assert.isTrue(isPSAStage(stage));
    });

    it('should identify PSA stage by stage_title', () => {
      const stage: Stage = {
        stage_title: 'PSA',
      };
      assert.isTrue(isPSAStage(stage));
    });

    it('should identify PSA stage by type', () => {
      const stage: Stage = {
        type: 'PSA',
      };
      assert.isTrue(isPSAStage(stage));
    });

    it('should return false for non-PSA stage', () => {
      const stage: Stage = {
        stage_type: 'IMPLEMENTATION_STARTED',
        stage_title: 'Implementation Started',
      };
      assert.isFalse(isPSAStage(stage));
    });

    it('should return false for undefined stage', () => {
      assert.isFalse(isPSAStage(undefined));
    });
  });

  describe('isPSAEmailPending', () => {
    it('should return true for PSA stage without intent_thread_url', () => {
      const stage: Stage = {
        stage_type: 'PSA',
        intent_thread_url: '',
      };
      assert.isTrue(isPSAEmailPending(stage));
    });

    it('should return true for PSA stage with null intent_thread_url', () => {
      const stage: Stage = {
        stage_type: 'PSA',
        intent_thread_url: undefined,
      };
      assert.isTrue(isPSAEmailPending(stage));
    });

    it('should return true for PSA stage with whitespace-only intent_thread_url', () => {
      const stage: Stage = {
        stage_type: 'PSA',
        intent_thread_url: '   ',
      };
      assert.isTrue(isPSAEmailPending(stage));
    });

    it('should return false for PSA stage with valid intent_thread_url', () => {
      const stage: Stage = {
        stage_type: 'PSA',
        intent_thread_url:
          'https://groups.google.com/a/chromium.org/g/blink-dev/c/abc123',
      };
      assert.isFalse(isPSAEmailPending(stage));
    });

    it('should return false for non-PSA stage', () => {
      const stage: Stage = {
        stage_type: 'IMPLEMENTATION_STARTED',
        intent_thread_url: '',
      };
      assert.isFalse(isPSAEmailPending(stage));
    });

    it('should return false for undefined stage', () => {
      assert.isFalse(isPSAEmailPending(undefined));
    });
  });

  describe('getPendingPSAStage', () => {
    it('should return the pending PSA stage', () => {
      const feature: Feature = {
        stages: [
          {
            stage_type: 'IMPLEMENTATION_STARTED',
            intent_thread_url: 'http://example.com',
          },
          {
            stage_type: 'PSA',
            intent_thread_url: '',
          },
        ],
      };
      const result = getPendingPSAStage(feature);
      assert.isNotNull(result);
      assert.equal(result?.stage_type, 'PSA');
    });

    it('should return undefined if no pending PSA stage', () => {
      const feature: Feature = {
        stages: [
          {
            stage_type: 'IMPLEMENTATION_STARTED',
            intent_thread_url: 'http://example.com',
          },
        ],
      };
      const result = getPendingPSAStage(feature);
      assert.isUndefined(result);
    });

    it('should return undefined for undefined feature', () => {
      const result = getPendingPSAStage(undefined);
      assert.isUndefined(result);
    });

    it('should return undefined for feature with no stages', () => {
      const feature: Feature = {
        stages: [],
      };
      const result = getPendingPSAStage(feature);
      assert.isUndefined(result);
    });
  });

  describe('hasPendingPSAEmail', () => {
    it('should return true if feature has pending PSA email', () => {
      const feature: Feature = {
        stages: [
          {
            stage_type: 'PSA',
            intent_thread_url: '',
          },
        ],
      };
      assert.isTrue(hasPendingPSAEmail(feature));
    });

    it('should return false if feature has no pending PSA email', () => {
      const feature: Feature = {
        stages: [
          {
            stage_type: 'PSA',
            intent_thread_url: 'http://example.com',
          },
        ],
      };
      assert.isFalse(hasPendingPSAEmail(feature));
    });

    it('should return false for undefined feature', () => {
      assert.isFalse(hasPendingPSAEmail(undefined));
    });
  });

  describe('getAllPendingPSAStages', () => {
    it('should return all pending PSA stages', () => {
      const feature: Feature = {
        stages: [
          {
            stage_type: 'PSA',
            intent_thread_url: '',
          },
          {
            stage_type: 'PSA',
            intent_thread_url: 'http://example.com',
          },
          {
            stage_type: 'PSA',
            intent_thread_url: '',
          },
        ],
      };
      const result = getAllPendingPSAStages(feature);
      assert.lengthOf(result, 2);
    });

    it('should return empty array if no pending PSA stages', () => {
      const feature: Feature = {
        stages: [
          {
            stage_type: 'IMPLEMENTATION_STARTED',
            intent_thread_url: '',
          },
        ],
      };
      const result = getAllPendingPSAStages(feature);
      assert.lengthOf(result, 0);
    });

    it('should return empty array for undefined feature', () => {
      const result = getAllPendingPSAStages(undefined);
      assert.lengthOf(result, 0);
    });
  });
});
