from flask import Blueprint, render_template, request, redirect, url_for, abort
from app.db.coverages import (
    get_coverage_by_id,
    list_coverages_by_patient,
    create_coverage,
    update_coverage,
    delete_coverage,
)
from app.db.patients import get_all_patients
from app.security.auth import login_required, role_required

coverages_bp = Blueprint("coverages", __name__, url_prefix="/admin/coverages")


@coverages_bp.route("/")
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def coverages_list():
    patients = get_all_patients()
    # show all coverages with patient detail
    coverages = []
    for p in patients:
        pkgs = list_coverages_by_patient(p['id'])
        for c in pkgs:
            coverages.append({
                **c,
                'patient_name': f"{p['first_name']} {p['last_name']}"
            })
    return render_template("admin/coverages_list.html", coverages=coverages)


@coverages_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def coverage_create():
    patients = get_all_patients()
    error = None

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        insurer_name = request.form.get("insurer_name")
        plan_name = request.form.get("plan_name")
        policy_number = request.form.get("policy_number")
        start_date = request.form.get("start_date")

        if not patient_id or not insurer_name or not plan_name or not policy_number or not start_date:
            error = "Todos los campos son obligatorios"
        else:
            coverage_id = create_coverage(
                patient_id=int(patient_id),
                insurer_name=insurer_name,
                plan_name=plan_name,
                policy_number=policy_number,
                group_number=None,
                insured_id=None,
                start_date=start_date,
                end_date=None,
            )
            return redirect(url_for("coverages.coverages_list"))

    return render_template("admin/coverage_form.html", patients=patients, error=error)


@coverages_bp.route("/<int:coverage_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def edit_coverage(coverage_id):
    coverage = get_coverage_by_id(coverage_id)
    if not coverage:
        return "Cobertura no encontrada", 404

    if request.method == "POST":
        insurer_name = request.form.get("insurer_name")
        plan_name = request.form.get("plan_name")
        policy_number = request.form.get("policy_number")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        update_coverage(
            coverage_id=coverage_id,
            insurer_name=insurer_name,
            plan_name=plan_name,
            policy_number=policy_number,
            group_number=coverage.get("group_number"),
            insured_id=coverage.get("insured_id"),
            start_date=start_date,
            end_date=end_date,
        )
        return redirect(url_for("coverages.coverages_list"))

    return render_template("admin/coverage_form.html", coverage=coverage)


@coverages_bp.route("/<int:coverage_id>/delete", methods=["POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def delete_coverage_route(coverage_id):
    delete_coverage(coverage_id)
    return redirect(url_for("coverages.coverages_list"))
