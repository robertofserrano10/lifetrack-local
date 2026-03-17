from flask import Blueprint, render_template, request, redirect, url_for
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
    coverages = []
    for p in patients:
        pkgs = list_coverages_by_patient(p['id'])
        for c in pkgs:
            coverages.append({**c, 'patient_name': f"{p['first_name']} {p['last_name']}"})
    return render_template("admin/coverages_list.html", coverages=coverages)


@coverages_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def coverage_create():
    patients = get_all_patients()
    error = None

    if request.method == "POST":
        patient_id   = request.form.get("patient_id")
        insurer_name = request.form.get("insurer_name")
        plan_name    = request.form.get("plan_name")
        policy_number = request.form.get("policy_number")
        start_date   = request.form.get("start_date")

        if not patient_id or not insurer_name or not plan_name or not policy_number or not start_date:
            error = "Paciente, aseguradora, plan, póliza y fecha de inicio son requeridos."
        else:
            create_coverage(
                patient_id=int(patient_id),
                insurer_name=insurer_name,
                plan_name=plan_name,
                policy_number=policy_number,
                group_number=request.form.get("group_number") or None,
                insured_id=request.form.get("insured_id") or None,
                start_date=start_date,
                end_date=request.form.get("end_date") or None,
                insured_first_name=request.form.get("insured_first_name") or None,
                insured_last_name=request.form.get("insured_last_name") or None,
                relationship_to_insured=request.form.get("relationship_to_insured") or "self",
                insured_address=request.form.get("insured_address") or None,
                insured_city=request.form.get("insured_city") or None,
                insured_state=request.form.get("insured_state") or None,
                insured_zip=request.form.get("insured_zip") or None,
                other_health_plan_11d=1 if request.form.get("other_health_plan_11d") else 0,
            )
            return redirect(url_for("coverages.coverages_list"))

    # Pre-select patient if coming from patient detail
    preselect_patient_id = request.args.get("patient_id")
    return render_template("admin/coverage_form.html", patients=patients, error=error,
                           preselect_patient_id=preselect_patient_id)


@coverages_bp.route("/<int:coverage_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def edit_coverage(coverage_id):
    coverage = get_coverage_by_id(coverage_id)
    if not coverage:
        return "Cobertura no encontrada", 404

    patients = get_all_patients()
    error = None

    if request.method == "POST":
        update_coverage(
            coverage_id=coverage_id,
            insurer_name=request.form.get("insurer_name"),
            plan_name=request.form.get("plan_name"),
            policy_number=request.form.get("policy_number"),
            group_number=request.form.get("group_number") or None,
            insured_id=request.form.get("insured_id") or None,
            start_date=request.form.get("start_date"),
            end_date=request.form.get("end_date") or None,
            insured_first_name=request.form.get("insured_first_name") or None,
            insured_last_name=request.form.get("insured_last_name") or None,
            relationship_to_insured=request.form.get("relationship_to_insured") or "self",
            insured_address=request.form.get("insured_address") or None,
            insured_city=request.form.get("insured_city") or None,
            insured_state=request.form.get("insured_state") or None,
            insured_zip=request.form.get("insured_zip") or None,
            other_health_plan_11d=1 if request.form.get("other_health_plan_11d") else 0,
        )
        return redirect(url_for("coverages.coverages_list"))

    return render_template("admin/coverage_form.html", coverage=coverage,
                           patients=patients, error=error)


@coverages_bp.route("/<int:coverage_id>/delete", methods=["POST"])
@login_required
@role_required("ADMIN", "FACTURADOR", "RECEPCION")
def delete_coverage_route(coverage_id):
    delete_coverage(coverage_id)
    return redirect(url_for("coverages.coverages_list"))