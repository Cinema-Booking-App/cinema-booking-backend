from app.core.database import Base
import pkgutil
import importlib

# Tự động import tất cả modules trong package hiện tại
package = __path__
for _, module_name, _ in pkgutil.iter_modules(package):
    importlib.import_module(f"{__name__}.{module_name}")
