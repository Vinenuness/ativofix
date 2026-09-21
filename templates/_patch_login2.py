# -*- coding: utf-8 -*-
"""Patch: rota /login2 (variante fullscreen) compartilhando a autenticacao do /login."""
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


OLD_BLOCK = '''@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"]) if limiter else lambda f: f
def login_page():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if not username or not password:
            return render_template("login.html", error="Informe usuário e senha")
        if len(username) > 120 or len(password) > 200:
            return render_template("login.html", error="Usuário ou senha inválidos")
        if username == LOGIN_USER and password == LOGIN_PASS:
            session.clear()
            session["logged_in"] = True
            session["user"] = username
            session["tenant_id"] = MASTER_TENANT_ID
            from time import time
            session["last_activity"] = time()
            logger.info(f"Login bem-sucedido: {username}")
            return redirect(url_for("index"))
        
        # Check tenant users
        with get_db() as conn:
            user = conn.execute(
                "SELECT user_id, tenant_id, password_hash FROM users WHERE lower(username) = lower(?) OR lower(email) = lower(?)",
                (username, username)
            ).fetchone()
            if user:
                import hashlib
                try:
                    is_valid = bcrypt.checkpw(password.encode(), user["password_hash"].encode())
                except Exception:
                    # Fallback: old SHA256 hash
                    import hashlib
                    is_valid = hashlib.sha256(password.encode()).hexdigest() == user["password_hash"]
                if is_valid:
                    session.clear()
                    session["logged_in"] = True
                    session["user"] = username
                    session["user_id"] = user["user_id"]
                    session["tenant_id"] = user["tenant_id"]
                    from time import time
                    session["last_activity"] = time()
                    # Migrate old SHA256 hash to bcrypt
                    if not user["password_hash"].startswith("$2"):
                        new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                        with get_db() as migrate_conn:
                            migrate_conn.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user["user_id"]))
                            migrate_conn.commit()
                    logger.info(f"Login bem-sucedido: {username} (tenant {user['tenant_id']})")
                    return redirect(url_for("index"))
        logger.warning(f"Tentativa de login falhou: {username}")
        return render_template("login.html", error="Usuário ou senha inválidos")
    if session.get("logged_in"):
        return redirect(url_for("index"))
    return render_template("login.html")'''

NEW_BLOCK = '''def _authenticate_request(username, password):
    """Valida credenciais (master ou usuario de tenant).

    Retorna None em caso de sucesso (sessao criada) ou a mensagem de erro.
    """
    if not username or not password:
        return "Informe usuário e senha"
    if len(username) > 120 or len(password) > 200:
        return "Usuário ou senha inválidos"
    if username == LOGIN_USER and password == LOGIN_PASS:
        session.clear()
        session["logged_in"] = True
        session["user"] = username
        session["tenant_id"] = MASTER_TENANT_ID
        from time import time
        session["last_activity"] = time()
        logger.info(f"Login bem-sucedido: {username}")
        return None

    # Check tenant users
    with get_db() as conn:
        user = conn.execute(
            "SELECT user_id, tenant_id, password_hash FROM users WHERE lower(username) = lower(?) OR lower(email) = lower(?)",
            (username, username)
        ).fetchone()
        if user:
            import hashlib
            try:
                is_valid = bcrypt.checkpw(password.encode(), user["password_hash"].encode())
            except Exception:
                # Fallback: old SHA256 hash
                import hashlib
                is_valid = hashlib.sha256(password.encode()).hexdigest() == user["password_hash"]
            if is_valid:
                session.clear()
                session["logged_in"] = True
                session["user"] = username
                session["user_id"] = user["user_id"]
                session["tenant_id"] = user["tenant_id"]
                from time import time
                session["last_activity"] = time()
                # Migrate old SHA256 hash to bcrypt
                if not user["password_hash"].startswith("$2"):
                    new_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    with get_db() as migrate_conn:
                        migrate_conn.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user["user_id"]))
                        migrate_conn.commit()
                logger.info(f"Login bem-sucedido: {username} (tenant {user['tenant_id']})")
                return None
    logger.warning(f"Tentativa de login falhou: {username}")
    return "Usuário ou senha inválidos"


def _render_login(template):
    """Fluxo comum de login (GET/POST) para as variantes de tela."""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        error = _authenticate_request(username, password)
        if error:
            return render_template(template, error=error)
        return redirect(url_for("index"))
    if session.get("logged_in"):
        return redirect(url_for("index"))
    return render_template(template)


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"]) if limiter else lambda f: f
def login_page():
    return _render_login("login.html")


@app.route("/login2", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"]) if limiter else lambda f: f
def login2_page():
    """Variante fullscreen: marca d'agua + card centralizado."""
    return _render_login("login2.html")'''

rep(OLD_BLOCK, NEW_BLOCK, count=1)

if s == orig:
    print("NOTHING CHANGED")
    sys.exit(1)
io.open(FP, "w", encoding="utf-8", newline="").write(s)
print("PATCH OK")
