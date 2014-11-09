# Base units
UNIT_GRAM = 'g'
UNIT_LITER = 'l'

# Derived units, only for display
UNIT_MILLILITER = 'ml'
UNIT_KILOGRAM  = 'kg'
UNIT_NONE = ''

UNITS = [UNIT_KILOGRAM, UNIT_GRAM,
         UNIT_LITER, UNIT_MILLILITER,
         UNIT_NONE]

DATABASE_UNITS = [UNIT_GRAM, UNIT_LITER, UNIT_NONE]

UNIT_CONVERSIONS = {
    (UNIT_KILOGRAM, UNIT_GRAM): lambda x: x * 1000,
    (UNIT_GRAM, UNIT_KILOGRAM): lambda x: x / 1000,

    (UNIT_LITER, UNIT_MILLILITER): lambda x: x * 1000,
    (UNIT_MILLILITER, UNIT_LITER): lambda x: x / 1000,
}

for u in UNITS:
    UNIT_CONVERSIONS[(u, u)] = lambda x: x

