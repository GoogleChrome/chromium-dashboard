# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Handler for displaying feature details via Server-Side Rendering (SSR)."""

from typing import Any

from api import converters
from framework import basehandlers
from internals import core_enums
from pages import form_definitions, form_field_specs

METADATA_FIELD_MAPPING: dict[str, str] = {
    'owner': 'owner_emails',
    'editors': 'editor_emails',
    'cc_recipients': 'cc_emails',
    'devrel': 'devrel_emails',
    'category': 'category_int',
    'feature_type': 'feature_type_int',
    'intent_stage': 'intent_stage_int',
    'tag_review_status': 'tag_review_status_int',
    'security_review_status': 'security_review_status_int',
    'privacy_review_status': 'privacy_review_status_int',
    'comments': 'feature_notes',
}

STAGE_FIELD_MAPPING: dict[str, str] = {
    'intent_to_implement_url': 'intent_thread_url',
    'intent_to_experiment_url': 'intent_thread_url',
    'intent_to_extend_experiment_url': 'intent_thread_url',
    'intent_to_ship_url': 'intent_thread_url',
    'dt_milestone_desktop_start': 'desktop_first',
    'dt_milestone_android_start': 'android_first',
    'dt_milestone_ios_start': 'ios_first',
    'dt_milestone_webview_start': 'webview_first',
    'ot_milestone_desktop_start': 'desktop_first',
    'ot_milestone_desktop_end': 'desktop_last',
    'ot_milestone_android_start': 'android_first',
    'ot_milestone_android_end': 'android_last',
    'ot_milestone_webview_start': 'webview_first',
    'ot_milestone_webview_end': 'webview_last',
    'shipped_milestone': 'desktop_first',
    'shipped_android_milestone': 'android_first',
    'shipped_ios_milestone': 'ios_first',
    'shipped_webview_milestone': 'webview_first',
    'rollout_milestone': 'desktop_first',
    'extension_desktop_last': 'desktop_last',
}


def _get_form_fields(form_def: Any) -> list[str]:
    """Flattens all fields across all sections in a FormDef, preserving order."""
    fields = []
    for section in form_def.get('sections', []):
        for field in section.get('fields', []):
            if field not in fields:
                fields.append(field)
    return fields


def _extract_field_value(
    field_name: str,
    primary_dict: Any,
    secondary_dict: Any = None,
    mapping_dict: dict[str, str] | None = None,
) -> Any:
    """Extracts a value for a field from primary or secondary dictionaries, supporting mapped fallback keys."""
    if mapping_dict and field_name in mapping_dict:
        mapped_key = mapping_dict[field_name]
        if mapped_key in primary_dict:
            return primary_dict[mapped_key]
        if secondary_dict and mapped_key in secondary_dict:
            return secondary_dict[mapped_key]

    if field_name in primary_dict:
        return primary_dict[field_name]
    if secondary_dict and field_name in secondary_dict:
        return secondary_dict[field_name]

    return None


class FeatureDetailHandler(basehandlers.FlaskHandler):
    """Handler for displaying feature details (SSR)."""

    HTTP_CACHE_TYPE = 'private'
    TEMPLATE_PATH = 'feature-detail.html'

    def get_template_data(self, **kwargs: Any) -> dict[str, Any]:
        """Returns template data or content for the feature detail page.

        Fetches the feature metadata and stages, and aggregates their fields
        according to the form definitions for the given feature type.
        """
        fe = self.get_specified_feature(**kwargs)
        fe_dict = converters.feature_entry_to_json_verbose(fe)

        # Select the appropriate metadata form definition based on feature type.
        if fe.feature_type == core_enums.FEATURE_TYPE_ENTERPRISE_ID:
            metadata_form = form_definitions.FLAT_ENTERPRISE_METADATA_FIELDS
        else:
            metadata_form = form_definitions.FLAT_METADATA_FIELDS

        # 1. Populate the metadata section with its appropriate fields.
        metadata_dict = {
            'id': fe_dict.get('id'),
            'feature_type_int': fe_dict.get('feature_type_int'),
            'feature_type': fe_dict.get('feature_type'),
            'intent_stage_int': fe_dict.get('intent_stage_int'),
            'intent_stage': fe_dict.get('intent_stage'),
            'active_stage_id': fe_dict.get('active_stage_id'),
            'deleted': fe_dict.get('deleted', False),
            'unlisted': fe_dict.get('unlisted', False),
            'star_count': fe_dict.get('star_count'),
            'accurate_as_of': fe_dict.get('accurate_as_of'),
            'markdown_fields': fe_dict.get('markdown_fields', []),
            'creator_email': fe_dict.get('creator_email'),
            'updater_email': fe_dict.get('updater_email'),
            'created': fe_dict.get('created'),
            'updated': fe_dict.get('updated'),
        }
        metadata_fields = _get_form_fields(metadata_form)
        for field in metadata_fields:
            metadata_dict[field] = _extract_field_value(
                field, fe_dict, None, METADATA_FIELD_MAPPING
            )

        # 2. Populate the stages list.
        # Flatten stages to include extension stages as separate dictionaries in the list.
        flattened_stages = []
        for s in fe_dict.get('stages', []):
            flattened_stages.append(s)
            for ext in s.get('extensions', []):
                flattened_stages.append(ext)

        output_stages = []
        for s in flattened_stages:
            stage_type = s.get('stage_type')
            stage_form = form_definitions.FORMS_BY_STAGE_TYPE.get(stage_type)

            stage_fields_dict = {
                'id': s.get('id'),
                'stage_type': stage_type,
                'display_name': s.get('display_name'),
                'feature_id': s.get('feature_id'),
                'intent_stage': s.get('intent_stage'),
                'stage_form': stage_form,
            }

            if stage_form:
                stage_fields = _get_form_fields(stage_form)
                for field in stage_fields:
                    stage_fields_dict[field] = _extract_field_value(
                        field, s, fe_dict, STAGE_FIELD_MAPPING
                    )
            else:
                # If no FormDef is mapped for this stage type, fallback to including the stage dict as-is.
                stage_fields_dict.update(s)

            output_stages.append(stage_fields_dict)

        return {
            'metadata': metadata_dict,
            'metadata_form': metadata_form,
            'stages': output_stages,
            'field_specs': form_field_specs.ALL_FIELDS,
        }
