# Base units
UNIT_GRAM = 'g'
UNIT_LITER = 'l'

# Derived units, only for display
UNIT_MILLILITER = 'ml'
UNIT_KILOGRAM  = 'kg'

UNITS = [UNIT_KILOGRAM, UNIT_GRAM,
         UNIT_LITER, UNIT_MILLILITER]

UNIT_CONVERSIONS = {
    (UNIT_LITER, UNIT_MILLILITER): lambda x: x * 1000,
    (UNIT_MILLILITER, UNIT_LITER): lambda x: x / 1000,
    (UNIT_KILOGRAM, UNIT_GRAM): lambda x: x * 1000,
    (UNIT_GRAM, UNIT_KILOGRAM): lambda x: x / 1000,
}

