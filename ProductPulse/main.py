from app import app
import logging
import routes.root
import routes.auth
import routes.admin
import routes.vehicles
import routes.damages
import routes.deliveries
import routes.loads
import routes.chat
import routes.driver

# Configure logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
