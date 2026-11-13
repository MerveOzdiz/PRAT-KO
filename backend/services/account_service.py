import hashlib
import re
import secrets
import time
from functools import wraps

import click
from flask.cli import with_appcontext
from flask import abort, current_app, g, session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from models.db import db


def account_credentials(data):
    email, password = data.get('email'), data.get('password')
    if not isinstance(email, str) or len(email.strip()) > 254 or not re.fullmatch(
        r'[^\s@]+@[^\s@]+\.[^\s@]+', email.strip()
    ):
        raise ValueError('Geçerli bir e-posta girin.')
    if not isinstance(password, str) or not 12 <= len(password) <= 128:
        raise ValueError('Parola 12–128 karakter olmalı.')
    return email.strip().lower(), password


def query_one(sql, **params):
    with db.engine.connect() as connection:
        return connection.execute(text(sql), params).mappings().first()


def query_all(sql, **params):
    with db.engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(sql), params).mappings()]


def create_account(email, password, role='USER'):
    password_hash = generate_password_hash(password)
    with db.engine.begin() as connection:
        return connection.execute(text("""
            INSERT INTO user_account (email, password_hash, role)
            VALUES (:email, :password_hash, :role)
        """), dict(email=email, password_hash=password_hash, role=role)).lastrowid


def session_digest(token):
    return hashlib.sha256(token.encode()).hexdigest() if isinstance(token, str) else None


def start_account_session(account_id):
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    expires = now + int(current_app.permanent_session_lifetime.total_seconds())
    with db.engine.begin() as connection:
        connection.execute(text("""
            DELETE FROM account_session WHERE expires_at <= :now OR token_hash = :old
        """), dict(now=now, old=session_digest(session.get('session_token'))))
        connection.execute(text("""
            INSERT INTO account_session (token_hash, account_id, expires_at)
            VALUES (:token_hash, :account_id, :expires)
        """), dict(token_hash=session_digest(token), account_id=account_id, expires=expires))
    session.clear()
    session.permanent = True
    session['session_token'] = token


def end_account_session():
    digest = session_digest(session.get('session_token'))
    if digest:
        with db.engine.begin() as connection:
            connection.execute(text('DELETE FROM account_session WHERE token_hash = :digest'), dict(digest=digest))
    session.clear()


def require_account(*roles):
    def decorate(view):
        @wraps(view)
        def checked(*args, **kwargs):
            g.session_digest = session_digest(session.get('session_token'))
            g.account = query_one("""
                SELECT account.id, account.email, account.role
                FROM account_session AS active
                JOIN user_account AS account ON account.id = active.account_id
                WHERE active.token_hash = :digest AND active.expires_at > :now
            """, digest=g.session_digest, now=int(time.time())) if g.session_digest else None
            if g.account is None:
                abort(401, 'Oturum açmanız gerekiyor.')
            if roles and g.account['role'] not in roles:
                abort(403, 'Bu işlem için yetkiniz yok.')
            return view(*args, **kwargs)
        return checked
    return decorate


def require_branch_owner(branch_id, connection=None):
    sql = """
        SELECT branch.id, branch.name, branch.address, branch.google_place_id
        FROM branch_membership JOIN branch ON branch.id = branch_membership.branch_id
        WHERE branch_membership.user_id = :user_id AND branch.id = :id AND branch.is_active = 1
    """
    params = dict(user_id=g.account['id'], id=branch_id)
    branch = (connection.execute(text(sql), params).mappings().first()
              if connection is not None else query_one(sql, **params))
    if g.account['role'] != 'OWNER' or branch is None:
        abort(403, 'Bu şube için yetkiniz yok.')
    return branch


@click.command('create-admin')
@click.argument('email')
@click.password_option(confirmation_prompt=True)
@with_appcontext
def create_admin(email, password):
    if db.engine.dialect.name != 'sqlite':
        raise click.ClickException('Bu aşamada hesap sistemi SQLite kullanır.')
    try:
        email, password = account_credentials(dict(email=email, password=password))
        create_account(email, password, 'ADMIN')
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    except IntegrityError as exc:
        raise click.ClickException('Bu e-posta zaten kayıtlı.') from exc
    click.echo('Yönetici hesabı oluşturuldu.')
