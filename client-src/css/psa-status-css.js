// Copyright 2024 Google Inc. All rights reserved.
// Use of this source code is governed by the Apache License 2.0 that can be
// found in the LICENSE file.

import {css} from 'lit';

export const PSA_STATUS_CSS = css`
  .psa-email-pending-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
    background-color: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
  }

  .feature-row-pending-psa {
    border-left: 4px solid #dc2626;
    background-color: #fffbfb;
  }

  .feature-row-pending-psa:hover {
    background-color: #fef2f2;
  }

  .psa-email-pending-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background-color: #fbbc04;
    color: #333;
    font-size: 10px;
    font-weight: bold;
    cursor: help;
    flex-shrink: 0;
  }

  @media (max-width: 768px) {
    .psa-email-pending-badge {
      padding: 0.375rem 0.5rem;
      font-size: 0.7rem;
    }

    .feature-row-pending-psa {
      border-left-width: 3px;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .psa-email-pending-icon {
      transition: none;
    }
  }
`;
