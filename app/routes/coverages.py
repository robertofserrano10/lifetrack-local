from flask import Blueprint, render_template
from app.db.coverages import get_coverage_by_id

coverages_bp = Blueprint("coverages", __name__, url_prefix="/coverages")


@coverages_bp.route("/<int:coverage_id>/edit")
def edit_coverage(coverage_id):
    coverage = get_coverage_by_id(coverage_id)
    if not coverage:
        return "Cobertura no encontrada", 404

    return render_template(
        "coverages/edit.html",
        coverage=coverage
    )
