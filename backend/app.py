from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import event
from werkzeug.serving import WSGIRequestHandler
from config.settings import Config
from models.db import db
from controllers.market_controller import market_bp
from controllers.category_controller import category_bp
from controllers.product_controller import product_bp
from controllers.provider_controller import provider_bp
from controllers.account_controller import account_bp
from controllers.owner_catalog_controller import catalog_bp
from controllers.price_review_controller import price_review_bp
from migrations import apply_sqlite_migrations
from services.account_service import create_admin
from services.product_comparison import normalize


account_bp.register_blueprint(catalog_bp)
account_bp.register_blueprint(price_review_bp)


def configure_sqlite(connection, _):
    connection.execute('PRAGMA foreign_keys = ON')
    connection.create_function('pratiko_normalize', 1, normalize, deterministic=True)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config.setdefault('CORS_ORIGINS', Config.CORS_ORIGINS)
    CORS(app, resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}},
         supports_credentials=True)
    db.init_app(app)
    app.register_blueprint(market_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(provider_bp)
    app.register_blueprint(account_bp)
    app.cli.add_command(create_admin)

    @app.route('/api/v1/health', methods=['GET'])
    def health_check():
        return jsonify(status='healthy', service='pratiko-backend')

    with app.app_context():
        if db.engine.dialect.name == 'sqlite':
            event.listen(db.engine, 'connect', configure_sqlite)
        db.create_all()
        apply_sqlite_migrations(db.engine)
    return app


class PratikoRequestHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        self.log('info', '%s %s %s', self.command, self.path.partition('?')[0], code)


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, request_handler=PratikoRequestHandler)
