// @ts-check

/** Represents an external organization that reviews Chromium changes. Currently the W3C TAG,
 * Firefox, and Safari. */
type LabelInfo = {
  description: string;
  variant: 'primary' | 'success' | 'neutral' | 'warning' | 'danger';
};

export class ExternalReviewer {
  icon: string;
  _labels: Record<string, LabelInfo>;
  /** Finds reviewer information based on their github repo name.
   *
   * @returns {ExternalReviewer | undefined} undefined if the repo doesn't hold external
   * reviewers.
   */
  static get(repo: string) {
    switch (repo) {
      case 'mozilla/standards-positions':
        return new ExternalReviewer(
          'https://avatars.githubusercontent.com/u/131524?s=48&v=4',
          {
            'position: defer': {description: 'Defer', variant: 'neutral'},
            'position: negative': {description: 'Negative', variant: 'danger'},
            'position: neutral': {description: 'Neutral', variant: 'neutral'},
            'position: positive': {description: 'Positive', variant: 'success'},
            'position: under consideration': {
              description: 'Under Consideration',
              variant: 'neutral',
            },
          }
        );

      case 'WebKit/standards-positions':
        return new ExternalReviewer(
          'https://avatars.githubusercontent.com/u/6458?s=48&v=4',
          {
            'position: oppose': {description: 'Oppose', variant: 'danger'},
            'position: neutral': {description: 'Neutral', variant: 'neutral'},
            'position: support': {description: 'Support', variant: 'success'},
          }
        );
      case 'w3ctag/design-reviews':
        return new ExternalReviewer(
          'https://avatars.githubusercontent.com/u/3874462?s=48&v=4',
          {
            'Resolution: ambivalent': {
              description: 'Ambivalent',
              variant: 'neutral',
            },
            'Resolution: decline': {description: 'Decline', variant: 'neutral'},
            'Resolution: lack of consensus': {
              description: 'Lack of Consensus',
              variant: 'neutral',
            },
            'Resolution: object': {description: 'Object', variant: 'danger'},
            'Resolution: out of scope': {
              description: 'Out of Scope',
              variant: 'neutral',
            },
            'Resolution: overtaken': {
              description: 'Overtaken',
              variant: 'warning',
            },
            'Resolution: satisfied with concerns': {
              description: 'Satisfied with Concerns',
              variant: 'warning',
            },
            'Resolution: satisfied': {
              description: 'Satisfied',
              variant: 'success',
            },
            'Resolution: timed out': {
              description: 'Timed Out',
              variant: 'warning',
            },
            'Resolution: too early': {
              description: 'Too Early',
              variant: 'warning',
            },
            'Resolution: unsatisfied': {
              description: 'Unsatisfied',
              variant: 'danger',
            },
            'Resolution: validated': {
              description: 'Early Review Validated',
              variant: 'warning',
            },
            'Resolution: withdrawn': {
              description: 'Withdrawn',
              variant: 'warning',
            },
          }
        );
    }
    return undefined;
  }

  /** Finds information about an issue label for this external reviewer.
   * @returns {LabelInfo}
   */
  label(name: string) {
    return this._labels[name];
  }

  constructor(icon: string, labels: Record<string, LabelInfo>) {
    this.icon = icon;
    this._labels = labels;
  }
}
