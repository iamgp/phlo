"""
Schema evolution and backward compatibility analysis.

Detects breaking vs safe schema changes and generates migration recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from phlo.contracts.schema import ColumnDefinition


class ChangeClassification(str, Enum):
    """Classification of schema changes."""

    SAFE = "safe"
    WARNING = "warning"
    BREAKING = "breaking"


@dataclass
class FieldChange:
    """Description of a change to a field."""

    field_name: str
    change_type: str  # "added", "removed", "modified"
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    classification: ChangeClassification = ChangeClassification.SAFE


@dataclass
class SchemaEvolutionAnalysis:
    """Results of schema evolution analysis."""

    classification: ChangeClassification
    changes: list[FieldChange]
    migration_recommendations: list[str] = None

    def __post_init__(self):
        if self.migration_recommendations is None:
            self.migration_recommendations = []


class SchemaEvolution:
    """
    Analyze schema evolution and classify changes.

    Determines if changes are backward compatible, breaking, or require warnings.
    """

    @staticmethod
    def analyze(
        old_columns: list[ColumnDefinition],
        new_columns: list[ColumnDefinition],
    ) -> SchemaEvolutionAnalysis:
        """
        Analyze changes between two schema versions.

        Args:
            old_columns: Previous schema columns
            new_columns: New schema columns

        Returns:
            Analysis with classification and recommendations
        """
        old_map = {col.name: col for col in old_columns}
        new_map = {col.name: col for col in new_columns}

        old_names = set(old_map.keys())
        new_names = set(new_map.keys())

        changes = []
        classification = ChangeClassification.SAFE

        # Detect added columns
        added = new_names - old_names
        for field_name in added:
            col = new_map[field_name]
            # Added nullable columns are safe
            if not col.required:
                changes.append(
                    FieldChange(
                        field_name=field_name,
                        change_type="added",
                        new_value=col.type,
                        classification=ChangeClassification.SAFE,
                    )
                )
            else:
                # Required added column needs migration
                changes.append(
                    FieldChange(
                        field_name=field_name,
                        change_type="added",
                        new_value=col.type,
                        classification=ChangeClassification.WARNING,
                    )
                )
                classification = ChangeClassification.WARNING

        # Detect removed columns
        removed = old_names - new_names
        for field_name in removed:
            changes.append(
                FieldChange(
                    field_name=field_name,
                    change_type="removed",
                    old_value=old_map[field_name].type,
                    classification=ChangeClassification.BREAKING,
                )
            )
            classification = ChangeClassification.BREAKING

        # Detect modified columns
        common = old_names & new_names
        for field_name in common:
            old_col = old_map[field_name]
            new_col = new_map[field_name]

            changes_in_col = []

            # Check type change
            if old_col.type != new_col.type:
                changes_in_col.append(
                    FieldChange(
                        field_name=field_name,
                        change_type="type_change",
                        old_value=old_col.type,
                        new_value=new_col.type,
                        classification=ChangeClassification.BREAKING,
                    )
                )
                classification = ChangeClassification.BREAKING

            # Check nullability change (required -> optional is safe, opposite is breaking)
            if old_col.required and not new_col.required:
                changes_in_col.append(
                    FieldChange(
                        field_name=field_name,
                        change_type="nullability_relaxed",
                        old_value="required",
                        new_value="optional",
                        classification=ChangeClassification.SAFE,
                    )
                )
            elif not old_col.required and new_col.required:
                changes_in_col.append(
                    FieldChange(
                        field_name=field_name,
                        change_type="nullability_tightened",
                        old_value="optional",
                        new_value="required",
                        classification=ChangeClassification.BREAKING,
                    )
                )
                classification = ChangeClassification.BREAKING

            changes.extend(changes_in_col)

        # Generate recommendations
        recommendations = SchemaEvolution._generate_recommendations(
            changes, classification
        )

        return SchemaEvolutionAnalysis(
            classification=classification,
            changes=changes,
            migration_recommendations=recommendations,
        )

    @staticmethod
    def _generate_recommendations(
        changes: list[FieldChange], classification: ChangeClassification
    ) -> list[str]:
        """Generate migration recommendations based on changes."""
        recommendations = []

        if classification == ChangeClassification.BREAKING:
            recommendations.append("Breaking changes detected - consumer approval required")
            recommendations.append("Consider using feature flags or dual writes during transition")

            removed_fields = [c for c in changes if c.change_type == "removed"]
            if removed_fields:
                fields = ", ".join([c.field_name for c in removed_fields])
                recommendations.append(
                    f"Plan consumer migration away from removed fields: {fields}"
                )

        elif classification == ChangeClassification.WARNING:
            recommendations.append("Warning: Changes may require consumer updates")
            recommendations.append("Recommend communicating with consumers before deployment")

            added_required = [
                c for c in changes
                if c.change_type == "added"
                and c.classification == ChangeClassification.WARNING
            ]
            if added_required:
                fields = ", ".join([c.field_name for c in added_required])
                recommendations.append(
                    f"Provide default values for required new fields: {fields}"
                )

        else:  # SAFE
            recommendations.append("Safe changes - no consumer action required")
            recommendations.append("Changes can be deployed without special coordination")

        return recommendations

    @staticmethod
    def is_backward_compatible(
        old_columns: list[ColumnDefinition],
        new_columns: list[ColumnDefinition],
    ) -> bool:
        """Check if changes are backward compatible."""
        analysis = SchemaEvolution.analyze(old_columns, new_columns)
        return analysis.classification in [ChangeClassification.SAFE]

    @staticmethod
    def get_breaking_changes(
        old_columns: list[ColumnDefinition],
        new_columns: list[ColumnDefinition],
    ) -> list[FieldChange]:
        """Get only breaking changes."""
        analysis = SchemaEvolution.analyze(old_columns, new_columns)
        return [
            c
            for c in analysis.changes
            if c.classification == ChangeClassification.BREAKING
        ]
