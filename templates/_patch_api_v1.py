# -*- coding: utf-8 -*-
"""Patch: API publica v1 com chaves por empresa (X-API-KEY).

- Tabela api_keys (hash SHA-256, raw mostrado uma unica vez)
- Helpers de autenticacao por chave (tenant isolado)
- Endpoints /api/v1/{ping,computers,units,locations,tickets} (GET)
- POST /api/v1/tickets (criar chamado pelo sistema da empresa)
- Gerenciamento de chaves: /api-docs (pagina) + /api/apikeys
"""
import io
import sys

FP = "server.py"
s = io.open(FP, encoding="utf-8", newline="").read()
orig = s
NL = "\r\n" if "\r\n" in s[:4000] else "\n"


def rep(old, new, count=1):
    global s
    old = old.replace("\n", NL)
    new = new.replace("\n", NL)
    n = s.count(old)
    if n != count:
        print(f"ANCHOR FAIL ({n}/{count}): {old[:70]!r}")
        sys.exit(1)
    s = s.replace(old, new, count)


# ---------- 1) Schema: tabela api_keys ----------
rep(
    "            CREATE TABLE IF NOT EXISTS locations (",
    """            CREATE TABLE IF NOT EXISTS api_keys (
                key_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                name TEXT,
                key_hash TEXT NOT NULL UNIQUE,
                prefix TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                last_used_at TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS locations (""",
    count=1,
)

# ---------- 2) Bloco da API v1 (antes da secao de PDF) ----------
rep(
    """# ================================
# API - EXPORT PDF (PCs POR UNIDADE)
# ================================""",
    """# ================================
# API PUBLICA v1 (integracao por chave X-API-KEY)
# ================================
import hashlib as _api_hashlib
import secrets as _api_secrets


def _hash_api_key(raw: str) -> str:
    return _api_hashlib.sha256(raw.encode()).hexdigest()


def _generate_api_key() -> str:
    return "afk_" + _api_secrets.token_hex(24)


def _auth_api_key():
    \"\"\"Valida o header X-API-KEY. Retorna (tenant_id, key_row) ou None.\"\"\"
    import hmac as _hmac
    raw = (request.headers.get("X-API-KEY") or "").strip()
    if not raw or len(raw) > 250 or not raw.startswith("afk_"):
        return None
    kh = _hash_api_key(raw)
    with get_db() as conn:
        row = conn.execute(
            "SELECT key_id, tenant_id, name, key_hash, prefix FROM api_keys WHERE active = 1 AND key_hash LIKE ?",
            (kh[:8] + "%",)
        ).fetchall()
    match = None
    for r in row:
        if _hmac.compare_digest(r["key_hash"], kh):
            match = r
            break
    if not match:
        return None
    with get_db() as conn:
        t = conn.execute("SELECT tenant_id FROM tenants WHERE tenant_id = ?", (match["tenant_id"],)).fetchone()
        if not t:
            return None
        conn.execute("UPDATE api_keys SET last_used_at = ? WHERE key_id = ?", (utc_now_iso(), match["key_id"]))
        conn.commit()
    return match["tenant_id"], match


def _api_auth_guard(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = _auth_api_key()
        if not auth:
            logger.warning(f"API v1: chave invalida/ausente de {request.remote_addr}")
            return jsonify({"error": "unauthorized", "hint": "envie o header X-API-KEY"}), 401
        request.api_tenant_id, request.api_key_row = auth
        return f(*args, **kwargs)
    return decorated


@app.route("/api/v1", methods=["GET"])
def api_v1_index():
    \"\"\"Auto-documentacao da API v1.\"\"\"
    return jsonify({
        "name": "AtivoFix API",
        "version": "1.0",
        "auth": "header X-API-KEY (chave por empresa)",
        "endpoints": {
            "GET /api/v1/ping": "teste de autenticacao",
            "GET /api/v1/computers?online=true|false": "maquinas da empresa",
            "GET /api/v1/units": "unidades + contagens",
            "GET /api/v1/locations?unit_id=N": "locais (opcionalmente por unidade)",
            "GET /api/v1/tickets?status=&from=AAAA-MM-DD&to=AAAA-MM-DD&limit=&offset=": "chamados",
            "POST /api/v1/tickets": "criar chamado {title, description, priority, cpf?, unit_id|unit_name, location_id?, tag_evo?}",
        },
    })


@app.route("/api/v1/ping")
@_api_auth_guard
def api_v1_ping():
    with get_db() as conn:
        t = conn.execute("SELECT name FROM tenants WHERE tenant_id = ?", (request.api_tenant_id,)).fetchone()
    return jsonify({"ok": True, "version": "1.0", "tenant": t["name"] if t else None})


@app.route("/api/v1/computers")
@_api_auth_guard
def api_v1_computers():
    flt = (request.args.get("online") or "").lower()
    with_payload = (request.args.get("payload") or "").lower() in ("1", "true", "yes")
    with get_db() as conn:
        rows = conn.execute(
            \"\"\"
            SELECT c.agent_id, c.hostname, c.alias, c.tag_evo, c.last_seen, c.payload_json,
                   u.unit_id, u.name AS unit_name, l.location_id, l.name AS location_name
            FROM computers c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN locations l ON c.location_id = l.location_id
            WHERE c.tenant_id = ?
            ORDER BY COALESCE(u.name, 'zzz'), c.hostname
            \"\"\",
            (request.api_tenant_id,),
        ).fetchall()
    now = datetime.now(timezone.utc)
    out = []
    for r in rows:
        online = False
        if r["last_seen"]:
            try:
                ls = datetime.fromisoformat(r["last_seen"].replace("Z", "+00:00"))
                if ls.tzinfo is None:
                    ls = ls.replace(tzinfo=timezone.utc)
                online = (now - ls).total_seconds() <= 180
            except Exception:
                online = False
        if flt == "true" and not online:
            continue
        if flt == "false" and online:
            continue
        item = {
            "agent_id": r["agent_id"],
            "hostname": r["hostname"],
            "alias": r["alias"],
            "tag_evo": r["tag_evo"],
            "online": online,
            "last_seen": r["last_seen"],
            "unit": {"id": r["unit_id"], "name": r["unit_name"]} if r["unit_id"] else None,
            "location": {"id": r["location_id"], "name": r["location_name"]} if r["location_id"] else None,
        }
        if with_payload and r["payload_json"]:
            try:
                item["hardware"] = json.loads(r["payload_json"])
            except Exception:
                pass
        out.append(item)
    return jsonify({"total": len(out), "computers": out})


@app.route("/api/v1/units")
@_api_auth_guard
def api_v1_units():
    with get_db() as conn:
        rows = conn.execute(
            \"\"\"
            SELECT u.unit_id, u.name, u.description,
                   (SELECT COUNT(*) FROM locations l WHERE l.unit_id = u.unit_id) AS locations_count,
                   (SELECT COUNT(*) FROM computers c WHERE c.unit_id = u.unit_id) AS computers_count
            FROM units u WHERE u.tenant_id = ? ORDER BY u.name
            \"\"\",
            (request.api_tenant_id,),
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/v1/locations")
@_api_auth_guard
def api_v1_locations():
    unit_id = request.args.get("unit_id")
    q = "SELECT location_id, unit_id, name, description FROM locations WHERE tenant_id = ?"
    params = [request.api_tenant_id]
    if unit_id:
        if not str(unit_id).isdigit():
            return jsonify({"error": "unit_id deve ser numero"}), 400
        q += " AND unit_id = ?"
        params.append(int(unit_id))
    q += " ORDER BY name"
    with get_db() as conn:
        rows = conn.execute(q, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/v1/tickets")
@_api_auth_guard
def api_v1_tickets():
    status = (request.args.get("status") or "").strip()
    d_from = (request.args.get("from") or "").strip()
    d_to = (request.args.get("to") or "").strip()
    limit = min(max(int(request.args.get("limit", 100)) if str(request.args.get("limit", "100")).isdigit() else 100, 1), 500)
    offset = max(int(request.args.get("offset", 0)) if str(request.args.get("offset", "0")).isdigit() else 0, 0)
    q = \"\"\"
        SELECT t.ticket_id, t.title, t.description, t.status, t.priority, t.category,
               t.created_by, t.assigned_to, t.created_at, t.updated_at, t.resolved_at,
               t.closed_at, t.sla_due, t.unit_id, u.name AS unit_name, t.location_id, l.name AS location_name,
               c.hostname, c.tag_evo
        FROM tickets t
        LEFT JOIN units u ON t.unit_id = u.unit_id
        LEFT JOIN locations l ON t.location_id = l.location_id
        LEFT JOIN computers c ON t.agent_id = c.agent_id
        WHERE t.tenant_id = ?
    \"\"\"
    params = [request.api_tenant_id]
    if status:
        q += " AND t.status = ?"
        params.append(status)
    if d_from:
        q += " AND t.created_at >= ?"
        params.append(d_from + "T00:00:00")
    if d_to:
        q += " AND t.created_at <= ?"
        params.append(d_to + "T23:59:59")
    with get_db() as conn:
        # contagem total com os mesmos filtros (sem paginacao)
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM tickets t WHERE t.tenant_id = ?" + (" AND t.status = ?" if status else "")
            + (" AND t.created_at >= ?" if d_from else "") + (" AND t.created_at <= ?" if d_to else ""),
            params,
        ).fetchone()["c"]
        q += " ORDER BY t.created_at DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = conn.execute(q, params).fetchall()
    return jsonify({"total": total, "returned": len(rows), "limit": limit, "offset": offset, "tickets": [dict(r) for r in rows]})


@app.route("/api/v1/tickets", methods=["POST"])
@_api_auth_guard
def api_v1_tickets_create():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    priority = (data.get("priority") or "medium").strip().lower()
    if priority not in ("low", "medium", "high", "critical"):
        return jsonify({"error": "priority deve ser low|medium|high|critical"}), 400
    if not title:
        return jsonify({"error": "title is required"}), 400
    if len(title) > 300 or len(description) > 20000:
        return jsonify({"error": "title/description muito longos"}), 400

    tid = request.api_tenant_id
    source = "api:" + (request.api_key_row["name"] or request.api_key_row["prefix"])
    cpf = _clean_cpf(data.get("cpf"))
    if cpf:
        cpf_err = _validate_cpf(cpf)
        if cpf_err:
            return jsonify({"error": cpf_err}), 400

    now = utc_now_iso()
    unit_id = None
    agent_id = None
    location_id = None
    with get_db() as conn:
        # unidade: id ou nome (case-insensitive, dentro da empresa da chave)
        if data.get("unit_id"):
            if not str(data["unit_id"]).isdigit():
                return jsonify({"error": "unit_id deve ser numero"}), 400
            r = conn.execute("SELECT unit_id FROM units WHERE unit_id = ? AND tenant_id = ?", (int(data["unit_id"]), tid)).fetchone()
            if not r:
                return jsonify({"error": "unit_id nao pertence a esta empresa"}), 400
            unit_id = r["unit_id"]
        elif data.get("unit_name"):
            r = conn.execute("SELECT unit_id FROM units WHERE tenant_id = ? AND lower(name) = lower(?)", (tid, str(data["unit_name"]).strip())).fetchone()
            if not r:
                return jsonify({"error": "unit_name nao encontrada nesta empresa"}), 404
            unit_id = r["unit_id"]

        # local: id ou nome (dentro da unidade)
        if data.get("location_id"):
            if not str(data["location_id"]).isdigit():
                return jsonify({"error": "location_id deve ser numero"}), 400
            r = conn.execute("SELECT location_id FROM locations WHERE location_id = ? AND tenant_id = ?", (int(data["location_id"]), tid)).fetchone()
            if not r:
                return jsonify({"error": "location_id nao pertence a esta empresa"}), 400
            location_id = r["location_id"]
        elif data.get("location_name") and unit_id:
            r = conn.execute("SELECT location_id FROM locations WHERE tenant_id = ? AND unit_id = ? AND lower(name) = lower(?)", (tid, unit_id, str(data["location_name"]).strip())).fetchone()
            if r:
                location_id = r["location_id"]

        # maquina: agent_id ou tag_evo (define unidade se ainda nao definida)
        if data.get("agent_id"):
            r = conn.execute("SELECT agent_id, unit_id FROM computers WHERE agent_id = ? AND tenant_id = ?", (data["agent_id"], tid)).fetchone()
            if r:
                agent_id = r["agent_id"]
                if unit_id is None and r["unit_id"]:
                    unit_id = r["unit_id"]
        elif data.get("tag_evo"):
            r = conn.execute("SELECT agent_id, unit_id FROM computers WHERE tag_evo = ? AND tenant_id = ?", (data["tag_evo"], tid)).fetchone()
            if r:
                agent_id = r["agent_id"]
                if unit_id is None and r["unit_id"]:
                    unit_id = r["unit_id"]

        conn.execute(
            "INSERT INTO tickets (tenant_id, agent_id, title, description, status, priority, created_by, cpf, unit_id, location_id, sla_due, created_at, updated_at) VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?, ?)",
            (tid, agent_id, title, description, priority, source, cpf, unit_id, location_id, sla_due_from(now, priority), now, now),
        )
        ticket_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
    try:
        notify_ticket_event(ticket_id, f"Novo chamado #{ticket_id}", title)
    except Exception:
        pass
    return jsonify({"ok": True, "ticket_id": ticket_id, "status": "open", "unit_id": unit_id, "location_id": location_id}), 201


# ---------- Gerenciamento de chaves (painel) ----------
@app.route("/api/apikeys", methods=["GET"])
@require_login
def api_apikeys_list():
    role, _ = current_user_access()
    if role != "master":
        return jsonify({"error": "sem permissao"}), 403
    with get_db() as conn:
        rows = conn.execute(
            \"\"\"
            SELECT k.key_id, k.tenant_id, t.name AS tenant_name, k.name, k.prefix, k.active, k.last_used_at, k.created_at,
                   (SELECT COUNT(*) FROM api_keys k2 WHERE k2.tenant_id = k.tenant_id AND k2.active = 1) AS active_in_tenant
            FROM api_keys k LEFT JOIN tenants t ON k.tenant_id = t.tenant_id
            ORDER BY k.created_at DESC
            \"\"\"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/apikeys", methods=["POST"])
@require_login
def api_apikeys_create():
    role, _ = current_user_access()
    if role != "master":
        return jsonify({"error": "sem permissao"}), 403
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name or len(name) > 80:
        return jsonify({"error": "informe um nome para a chave"}), 400
    tid = data.get("tenant_id")
    if tid is None or not str(tid).isdigit():
        tid = get_current_tenant()
    tid = int(tid)
    with get_db() as conn:
        if not conn.execute("SELECT tenant_id FROM tenants WHERE tenant_id = ?", (tid,)).fetchone():
            return jsonify({"error": "empresa nao encontrada"}), 404
        if conn.execute("SELECT COUNT(*) AS c FROM api_keys WHERE tenant_id = ? AND active = 1", (tid,)).fetchone()["c"] >= 20:
            return jsonify({"error": "limite de 20 chaves ativas por empresa"}), 400
        raw = _generate_api_key()
        kh = _hash_api_key(raw)
        conn.execute(
            "INSERT INTO api_keys (tenant_id, name, key_hash, prefix, active, created_at) VALUES (?, ?, ?, ?, 1, ?)",
            (tid, name, kh, raw[:12], utc_now_iso()),
        )
        key_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        tname = conn.execute("SELECT name FROM tenants WHERE tenant_id = ?", (tid,)).fetchone()["name"]
        conn.commit()
    logger.info(f"API key criada: {name} (tenant {tid}) por {session.get('user')}")
    # raw aparece APENAS aqui — nunca mais e possivel recupera-lo
    return jsonify({"ok": True, "key_id": key_id, "key": raw, "prefix": raw[:12], "tenant_id": tid, "tenant_name": tname, "name": name})


@app.route("/api/apikeys/<int:key_id>", methods=["DELETE"])
@require_login
def api_apikeys_delete(key_id):
    role, _ = current_user_access()
    if role != "master":
        return jsonify({"error": "sem permissao"}), 403
    with get_db() as conn:
        conn.execute("DELETE FROM api_keys WHERE key_id = ?", (key_id,))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/apikeys/<int:key_id>/toggle", methods=["POST"])
@require_login
def api_apikeys_toggle(key_id):
    role, _ = current_user_access()
    if role != "master":
        return jsonify({"error": "sem permissao"}), 403
    with get_db() as conn:
        row = conn.execute("SELECT active FROM api_keys WHERE key_id = ?", (key_id,)).fetchone()
        if not row:
            return jsonify({"error": "chave nao encontrada"}), 404
        newv = 0 if row["active"] else 1
        conn.execute("UPDATE api_keys SET active = ? WHERE key_id = ?", (newv, key_id))
        conn.commit()
    return jsonify({"ok": True, "active": bool(newv)})


# ================================
# API - EXPORT PDF (PCs POR UNIDADE)
# ================================""",
    count=1,
)

# ---------- 3) Pagina /api-docs ----------
rep(
    '''@app.route("/chamados")
@require_login
def chamados_page():
    return render_template("chamados.html")''',
    '''@app.route("/chamados")
@require_login
def chamados_page():
    return render_template("chamados.html")


@app.route("/api-docs")
@require_login
def api_docs_page():
    return render_template("api.html")''',
    count=1,
)

if s == orig:
    print("NOTHING CHANGED")
    sys.exit(1)
io.open(FP, "w", encoding="utf-8", newline="").write(s)
print("PATCH OK")
