# Base units
UNIT_GRAMM = 'g'
UNIT_LITER = 'l'

# Derived units, only for display
UNIT_MILLILITER = 'ml'
UNIT_KILOGRAMM  = 'kg'

UNIT_CONVERSIONS = {
    (UNIT_LITER, UNIT_MILLILITER): lambda x: x * 1000,
    (UNIT_MILLILITER, UNIT_LITER): lambda x: x / 1000,
    (UNIT_KILOGRAMM, UNIT_GRAMM): lambda x: x * 1000,
    (UNIT_GRAMM, UNIT_KILOGRAMM): lambda x: x / 1000,
}

