from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from literary_calendar_database import LiteraryCalendarDatabase
from time_utils import now_tz


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["DB_PATH"] = db_path or os.getenv("DB_PATH", "literary_events.db")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/events", methods=["GET", "POST"])
    def api_events():
        if request.method == "GET":
            try:
                db = LiteraryCalendarDatabase(app.config["DB_PATH"])
                conn = db.conn
                c = conn.cursor()

                month = request.args.get("month")
                if month:
                    month_str = f"{int(month):02d}"
                    c.execute(
                        "SELECT id, event_date, title, description, year FROM events WHERE event_date LIKE ? ORDER BY event_date",
                        (f"{month_str}-%",),
                    )
                else:
                    c.execute(
                        "SELECT id, event_date, title, description, year FROM events ORDER BY event_date"
                    )

                events = []
                for row in c.fetchall():
                    event_id = row[0]
                    c.execute(
                        "SELECT COUNT(*) FROM event_references WHERE event_id = ?",
                        (event_id,),
                    )
                    refs_count = c.fetchone()[0]

                    events.append(
                        {
                            "id": event_id,
                            "event_date": row[1],
                            "title": row[2],
                            "description": row[3],
                            "year": row[4],
                            "references_count": refs_count,
                        }
                    )

                if not month:
                    c.execute("SELECT COUNT(*) FROM events")
                    total_events = c.fetchone()[0]

                    tz = os.getenv("TIMEZONE", "Europe/Moscow")
                    today = now_tz(tz)
                    today_str = f"{today.month:02d}-{today.day:02d}"
                    c.execute("SELECT COUNT(*) FROM events WHERE event_date = ?", (today_str,))
                    today_events = c.fetchone()[0]

                    c.execute("SELECT COUNT(*) FROM event_references")
                    total_references = c.fetchone()[0]

                    stats = {
                        "total_events": total_events,
                        "today_events": today_events,
                        "total_references": total_references,
                    }
                else:
                    stats = {}

                db.close()
                return jsonify({"events": events, "stats": stats})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # POST
        try:
            data = request.json
            db = LiteraryCalendarDatabase(app.config["DB_PATH"])

            year_value = data.get("year")
            if isinstance(year_value, str):
                year_value = year_value.strip()
            year_value = year_value or None

            event_id = db.add_event(
                month=int(data["month"]),
                day=int(data["day"]),
                event_type=data.get("event_type", "литературное событие"),
                title=data["title"],
                description=data.get("description", ""),
                author_name="",
                book_title="",
                year=year_value,
            )

            db.close()
            return jsonify({"success": True, "id": event_id})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400

    @app.route("/api/events/<int:event_id>", methods=["GET", "PUT", "DELETE"])
    def api_event(event_id: int):
        try:
            db = LiteraryCalendarDatabase(app.config["DB_PATH"])
            conn = db.conn
            c = conn.cursor()

            if request.method == "GET":
                c.execute(
                    "SELECT id, event_date, title, description, author_name, book_title, year FROM events WHERE id = ?",
                    (event_id,),
                )
                event = c.fetchone()
                db.close()
                if event:
                    return jsonify(
                        dict(
                            zip(
                                [
                                    "id",
                                    "event_date",
                                    "title",
                                    "description",
                                    "author_name",
                                    "book_title",
                                    "year",
                                ],
                                event,
                            )
                        )
                    )
                return jsonify({"error": "Not found"}), 404

            if request.method == "PUT":
                data = request.json
                year_value = data.get("year")
                if isinstance(year_value, str):
                    year_value = year_value.strip()
                year_value = year_value or None
                c.execute(
                    "UPDATE events SET title = ?, description = ?, year = ? WHERE id = ?",
                    (data["title"], data.get("description", ""), year_value, event_id),
                )
                conn.commit()
                db.close()
                return jsonify({"success": True})

            # DELETE
            c.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()
            db.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/events/<int:event_id>/references", methods=["GET"])
    def api_event_references(event_id: int):
        try:
            db = LiteraryCalendarDatabase(app.config["DB_PATH"])
            conn = db.conn
            c = conn.cursor()

            c.execute("SELECT * FROM event_references WHERE event_id = ?", (event_id,))
            references = [
                dict(
                    zip(
                        [
                            "id",
                            "event_id",
                            "reference_type",
                            "reference_uuid",
                            "reference_slug",
                            "reference_name",
                            "priority",
                            "metadata",
                        ],
                        row,
                    )
                )
                for row in c.fetchall()
            ]

            db.close()
            return jsonify({"references": references})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/references", methods=["POST"])
    def api_add_reference():
        try:
            data = request.json
            db = LiteraryCalendarDatabase(app.config["DB_PATH"])

            ref_uuid = data.get("reference_uuid", "")
            if ref_uuid == "auto" or not ref_uuid:
                ref_uuid = f"{data['reference_type']}-{data['reference_name'].lower().replace(' ', '-')}"

            ref_slug = data.get("reference_slug", "")
            if not ref_slug:
                ref_slug = ref_uuid.lower() if ref_uuid else ""

            db.add_reference(
                event_id=int(data["event_id"]),
                reference_type=data["reference_type"],
                reference_uuid=ref_uuid,
                reference_slug=ref_slug,
                reference_name=data["reference_name"],
                priority=1,
            )

            db.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400

    @app.route("/api/references/<int:ref_id>", methods=["DELETE", "PUT"])
    def api_delete_or_update_reference(ref_id: int):
        try:
            db = LiteraryCalendarDatabase(app.config["DB_PATH"])
            conn = db.conn
            c = conn.cursor()

            if request.method == "DELETE":
                c.execute("DELETE FROM event_references WHERE id = ?", (ref_id,))
                conn.commit()
                db.close()
                return jsonify({"success": True})

            data = request.json
            ref_uuid = data.get("reference_uuid", "")
            ref_slug = data.get("reference_slug", "")
            if not ref_slug and ref_uuid:
                ref_slug = ref_uuid.lower()

            c.execute(
                """UPDATE event_references
                         SET reference_type = ?, reference_name = ?, reference_uuid = ?, reference_slug = ?
                         WHERE id = ?""",
                (
                    data["reference_type"],
                    data["reference_name"],
                    ref_uuid,
                    ref_slug,
                    ref_id,
                ),
            )
            conn.commit()
            db.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app

