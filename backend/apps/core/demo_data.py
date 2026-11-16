"""Demo catalog and users loaded by `manage.py seed_demo` (development only)."""

DEMO_PASSWORD = "entrenanutricion#2025"

STAFF_USERS = [
    # (email, first_name, last_name, role)
    ("admin@entrenanutricion.dev", "Laura", "Admin", "admin"),
    ("trainer@entrenanutricion.dev", "Marc", "Vidal", "trainer"),
    ("nutri@entrenanutricion.dev", "Elena", "Soler", "nutritionist"),
]

# (name, muscle group slugs, description, steps, technique, common mistakes, benefits)
EXERCISES = [
    (
        "Press de banca",
        ["chest", "triceps", "shoulders"],
        "Empuje horizontal con barra tumbado en un banco plano.",
        [
            "Túmbate con los ojos bajo la barra y los pies firmes en el suelo.",
            "Agarra la barra algo más abierto que los hombros y desciéndela al pecho.",
            "Empuja hasta extender los codos sin bloquearlos.",
        ],
        "Escápulas retraídas, ligero arco lumbar y codos a unos 45° del torso.",
        "Rebotar la barra en el pecho y despegar los glúteos del banco.",
        "Desarrolla la fuerza y el volumen del pectoral, el deltoides anterior y el tríceps.",
    ),
    (
        "Flexiones",
        ["chest", "triceps", "abs"],
        "Empuje con el peso corporal desde el suelo.",
        [
            "Apoya las manos a la anchura de los hombros y estira el cuerpo.",
            "Baja el pecho hasta casi tocar el suelo.",
            "Empuja el suelo para volver arriba.",
        ],
        "Cuerpo en línea recta de la cabeza a los talones, abdomen activo.",
        "Hundir la cadera o abrir demasiado los codos.",
        "Fuerza de empuje sin material y estabilidad del tronco.",
    ),
    (
        "Aperturas con mancuernas",
        ["chest"],
        "Aislamiento del pectoral en banco plano.",
        [
            "Túmbate con las mancuernas sobre el pecho y los codos ligeramente flexionados.",
            "Abre los brazos en arco hasta notar estiramiento en el pecho.",
            "Cierra el arco hasta juntar las mancuernas.",
        ],
        "Mantén el mismo ángulo de codo durante todo el recorrido.",
        "Convertir el movimiento en un press o bajar demasiado.",
        "Mejora el rango de movimiento y la conexión con el pectoral.",
    ),
    (
        "Fondos en paralelas",
        ["triceps", "chest"],
        "Empuje vertical con el peso corporal.",
        [
            "Sujétate en las paralelas con los brazos extendidos.",
            "Flexiona los codos hasta que los hombros queden a la altura de los codos.",
            "Empuja hasta extender los brazos.",
        ],
        "Torso ligeramente inclinado y hombros lejos de las orejas.",
        "Bajar demasiado y forzar el hombro.",
        "Tríceps y pectoral inferior fuertes con poco material.",
    ),
    (
        "Press francés",
        ["triceps"],
        "Extensión de codos tumbado con barra Z.",
        [
            "Túmbate con la barra sobre la frente y los brazos verticales.",
            "Flexiona los codos llevando la barra hacia la frente.",
            "Extiende los codos para volver arriba.",
        ],
        "Codos fijos y apuntando al techo.",
        "Abrir los codos o mover los hombros.",
        "Trabaja la cabeza larga del tríceps.",
    ),
    (
        "Extensión de tríceps en polea",
        ["triceps"],
        "Extensión de codos de pie en polea alta.",
        [
            "Agarra la cuerda con los codos pegados al cuerpo.",
            "Extiende los codos separando la cuerda al final.",
            "Vuelve despacio a la posición inicial.",
        ],
        "Solo se mueven los antebrazos.",
        "Inclinar el cuerpo para mover más peso.",
        "Aislamiento seguro del tríceps.",
    ),
    (
        "Dominadas",
        ["lats", "biceps"],
        "Tracción vertical colgado de una barra.",
        [
            "Cuélgate con agarre prono algo más ancho que los hombros.",
            "Tira de los codos hacia abajo hasta pasar la barbilla de la barra.",
            "Desciende controlando hasta extender los brazos.",
        ],
        "Inicia el movimiento bajando las escápulas.",
        "Balancearse o hacer medio recorrido.",
        "Espalda ancha y fuerte; gran ejercicio de fuerza relativa.",
    ),
    (
        "Remo con barra",
        ["lats", "traps", "biceps"],
        "Tracción horizontal con el torso inclinado.",
        [
            "Inclina el torso unos 45° con la espalda neutra.",
            "Tira de la barra hacia el ombligo.",
            "Baja la barra con control.",
        ],
        "Espalda neutra y abdomen firme durante todo el movimiento.",
        "Redondear la espalda o tirar con impulso.",
        "Grosor de espalda y salud postural.",
    ),
    (
        "Jalón al pecho",
        ["lats", "biceps"],
        "Tracción vertical en polea alta.",
        [
            "Siéntate con los muslos bajo los rodillos y agarra la barra.",
            "Tira de la barra hasta la parte alta del pecho.",
            "Sube controlando hasta estirar los brazos.",
        ],
        "Pecho alto y codos hacia abajo y atrás.",
        "Tirar por detrás de la nuca o echarse muy atrás.",
        "Alternativa progresiva a las dominadas.",
    ),
    (
        "Curl de bíceps con barra",
        ["biceps", "forearms"],
        "Flexión de codos de pie con barra.",
        [
            "Sujeta la barra con agarre supino a la anchura de los hombros.",
            "Flexiona los codos sin moverlos de los costados.",
            "Baja despacio hasta extender los brazos.",
        ],
        "Codos fijos y muñecas neutras.",
        "Balancear el cuerpo para subir la barra.",
        "Fuerza y volumen del bíceps.",
    ),
    (
        "Curl martillo",
        ["biceps", "forearms"],
        "Flexión de codos con agarre neutro.",
        [
            "Sujeta las mancuernas con las palmas enfrentadas.",
            "Flexiona los codos alternando o a la vez.",
            "Baja con control.",
        ],
        "Mantén el agarre neutro todo el recorrido.",
        "Usar impulso de la espalda.",
        "Trabaja braquial y antebrazo.",
    ),
    (
        "Press militar",
        ["shoulders", "triceps"],
        "Empuje vertical de pie con barra.",
        [
            "Coloca la barra a la altura de las clavículas.",
            "Empuja la barra por encima de la cabeza.",
            "Baja hasta las clavículas con control.",
        ],
        "Glúteos y abdomen contraídos para no arquear la espalda.",
        "Hiperextender la zona lumbar.",
        "Hombros fuertes y estabilidad del tronco.",
    ),
    (
        "Elevaciones laterales",
        ["shoulders"],
        "Aislamiento del deltoides lateral con mancuernas.",
        [
            "De pie, mancuernas a los lados y codos algo flexionados.",
            "Eleva los brazos hasta la altura de los hombros.",
            "Baja despacio.",
        ],
        "Lidera el movimiento con los codos, no con las manos.",
        "Subir por encima de los hombros o con impulso.",
        "Hombros más anchos y equilibrados.",
    ),
    (
        "Encogimientos con mancuernas",
        ["traps"],
        "Elevación de hombros con carga.",
        [
            "De pie, sujeta las mancuernas a los lados.",
            "Eleva los hombros hacia las orejas.",
            "Mantén un segundo arriba y baja.",
        ],
        "Movimiento vertical, sin rotar los hombros.",
        "Mover la cabeza hacia delante.",
        "Trapecio superior fuerte.",
    ),
    (
        "Sentadilla",
        ["quadriceps", "glutes"],
        "Flexión de rodillas y cadera con barra en la espalda.",
        [
            "Coloca la barra sobre los trapecios y los pies a la anchura de los hombros.",
            "Baja flexionando rodillas y cadera hasta romper el paralelo.",
            "Empuja el suelo para subir.",
        ],
        "Rodillas en la dirección de las puntas de los pies y espalda neutra.",
        "Levantar los talones o juntar las rodillas.",
        "Fuerza global del tren inferior.",
    ),
    (
        "Zancadas",
        ["quadriceps", "glutes", "hamstrings"],
        "Desplazamiento con flexión de ambas rodillas.",
        [
            "Da un paso largo hacia delante.",
            "Baja hasta que la rodilla trasera casi toque el suelo.",
            "Empuja con la pierna delantera para volver.",
        ],
        "Torso erguido y rodilla delantera estable.",
        "Pasos cortos que cargan la rodilla.",
        "Fuerza unilateral y equilibrio.",
    ),
    (
        "Peso muerto rumano",
        ["hamstrings", "glutes", "lower_back"],
        "Bisagra de cadera con barra.",
        [
            "De pie, barra frente a los muslos y rodillas ligeramente flexionadas.",
            "Lleva la cadera atrás bajando la barra pegada a las piernas.",
            "Vuelve empujando la cadera hacia delante.",
        ],
        "Espalda neutra y barra siempre cerca del cuerpo.",
        "Redondear la espalda o flexionar demasiado las rodillas.",
        "Isquiotibiales y glúteos fuertes, mejor bisagra de cadera.",
    ),
    (
        "Prensa de piernas",
        ["quadriceps", "glutes"],
        "Empuje de piernas en máquina.",
        [
            "Siéntate y apoya los pies en la plataforma.",
            "Baja la plataforma flexionando las rodillas.",
            "Empuja sin bloquear las rodillas.",
        ],
        "Zona lumbar siempre apoyada en el respaldo.",
        "Bajar tanto que la pelvis se despegue.",
        "Volumen de cuádriceps con baja demanda técnica.",
    ),
    (
        "Elevación de gemelos",
        ["calves"],
        "Extensión de tobillos de pie.",
        [
            "Apoya la punta de los pies en un escalón.",
            "Sube sobre las puntas lo más alto posible.",
            "Baja hasta notar estiramiento.",
        ],
        "Recorrido completo y pausa arriba.",
        "Rebotar en la parte baja.",
        "Gemelos fuertes y tobillos estables.",
    ),
    (
        "Hip thrust",
        ["glutes", "hamstrings"],
        "Extensión de cadera con la espalda apoyada en un banco.",
        [
            "Apoya la parte alta de la espalda en el banco y la barra en la cadera.",
            "Empuja la cadera hacia arriba hasta alinear rodillas, cadera y hombros.",
            "Baja la cadera con control.",
        ],
        "Barbilla recogida y pelvis en retroversión arriba.",
        "Arquear la zona lumbar en lugar de extender la cadera.",
        "El ejercicio más directo para el glúteo mayor.",
    ),
    (
        "Plancha",
        ["abs", "lower_back"],
        "Isometría de tronco sobre antebrazos.",
        [
            "Apoya antebrazos y puntas de los pies.",
            "Alinea cabeza, cadera y talones.",
            "Mantén la posición respirando con normalidad.",
        ],
        "Abdomen y glúteos activos; no hundas la cadera.",
        "Elevar demasiado la cadera o aguantar la respiración.",
        "Estabilidad del core y protección lumbar.",
    ),
    (
        "Crunch abdominal",
        ["abs"],
        "Flexión de tronco tumbado.",
        [
            "Túmbate con rodillas flexionadas y manos junto a las sienes.",
            "Eleva los hombros del suelo contrayendo el abdomen.",
            "Baja despacio.",
        ],
        "Mueve el tronco, no tires del cuello.",
        "Impulsarse con los brazos.",
        "Fortalece el recto abdominal.",
    ),
    (
        "Elevación de piernas colgado",
        ["abs", "forearms"],
        "Flexión de cadera colgado de una barra.",
        [
            "Cuélgate de la barra con los brazos extendidos.",
            "Eleva las piernas hasta la horizontal.",
            "Baja sin balancearte.",
        ],
        "Controla el balanceo activando el abdomen.",
        "Usar el impulso de las piernas.",
        "Abdomen inferior y fuerza de agarre.",
    ),
    (
        "Hiperextensiones lumbares",
        ["lower_back", "glutes"],
        "Extensión de tronco en banco romano.",
        [
            "Colócate en el banco con la cadera en el borde del apoyo.",
            "Baja el tronco con la espalda neutra.",
            "Sube hasta alinear el tronco con las piernas.",
        ],
        "No sobrepases la línea del cuerpo al subir.",
        "Hiperextender la columna arriba.",
        "Zona lumbar resistente.",
    ),
    (
        "Burpees",
        ["quadriceps", "chest", "abs"],
        "Ejercicio metabólico de cuerpo completo.",
        [
            "Desde de pie, apoya las manos y lleva los pies atrás.",
            "Haz una flexión y recoge los pies.",
            "Salta con los brazos arriba.",
        ],
        "Mantén el ritmo sin perder la alineación en la plancha.",
        "Hundir la cadera al saltar atrás.",
        "Mejora la condición cardiovascular y la potencia.",
    ),
]

# (name, description, [(exercise name, sets, reps, rest seconds)])
WORKOUTS = [
    (
        "Core",
        "Estabilidad y fuerza del tronco.",
        [
            ("Plancha", 3, 1, 45),
            ("Crunch abdominal", 3, 15, 45),
            ("Elevación de piernas colgado", 3, 10, 60),
            ("Hiperextensiones lumbares", 3, 12, 60),
        ],
    ),
    (
        "Piernas",
        "Tren inferior completo.",
        [
            ("Sentadilla", 4, 8, 120),
            ("Zancadas", 3, 10, 90),
            ("Peso muerto rumano", 3, 10, 90),
            ("Prensa de piernas", 3, 12, 90),
            ("Elevación de gemelos", 4, 15, 45),
        ],
    ),
    (
        "Espalda y bíceps",
        "Tracciones y flexores del codo.",
        [
            ("Dominadas", 4, 6, 120),
            ("Remo con barra", 4, 8, 90),
            ("Jalón al pecho", 3, 10, 75),
            ("Curl de bíceps con barra", 3, 10, 60),
            ("Curl martillo", 3, 12, 60),
        ],
    ),
    (
        "Pecho y tríceps",
        "Empujes horizontales y extensión de codos.",
        [
            ("Press de banca", 4, 8, 120),
            ("Aperturas con mancuernas", 3, 12, 60),
            ("Fondos en paralelas", 3, 10, 90),
            ("Press francés", 3, 10, 60),
            ("Extensión de tríceps en polea", 3, 12, 60),
        ],
    ),
    (
        "Hombro",
        "Deltoides y trapecio.",
        [
            ("Press militar", 4, 8, 120),
            ("Elevaciones laterales", 4, 12, 60),
            ("Encogimientos con mancuernas", 3, 12, 60),
        ],
    ),
    (
        "Full body",
        "Sesión de cuerpo completo.",
        [
            ("Burpees", 3, 10, 60),
            ("Sentadilla", 3, 10, 90),
            ("Flexiones", 3, 12, 60),
            ("Remo con barra", 3, 10, 90),
            ("Hip thrust", 3, 12, 75),
            ("Plancha", 3, 1, 45),
        ],
    ),
]

# (name, description, goal, difficulty, equipment, weeks, [workout names in order])
TRAINING_PLANS = [
    (
        "Iniciación full body",
        "Tres sesiones semanales para crear el hábito y aprender la técnica básica.",
        "maintain",
        "beginner",
        "free_weights",
        12,
        ["Full body", "Core", "Full body"],
    ),
    (
        "Hipertrofia 4 días",
        "Rutina dividida por grupos musculares para ganar masa muscular.",
        "gain_muscle",
        "intermediate",
        "full_gym",
        10,
        ["Pecho y tríceps", "Espalda y bíceps", "Piernas", "Hombro"],
    ),
    (
        "Quema grasa 3 días",
        "Sesiones metabólicas y de fuerza para perder grasa conservando músculo.",
        "lose_weight",
        "beginner",
        "full_gym",
        8,
        ["Full body", "Piernas", "Core"],
    ),
]

# (name, category, diet_label, kcal, proteins g, carbs g, fats g, distribution, description)
MEAL_PLANS = [
    (
        "Déficit moderado alto en proteínas",
        "weight_loss",
        "high_protein",
        1700,
        150,
        150,
        55,
        {"breakfast": 20, "lunch": 30, "dinner": 30, "snacks": 20},
        "Déficit de unas 400 kcal con proteína alta para preservar la masa muscular.",
    ),
    (
        "Déficit mediterráneo",
        "weight_loss",
        "mediterranean",
        1700,
        110,
        180,
        60,
        {"breakfast": 25, "lunch": 35, "dinner": 30, "snacks": 10},
        "Verdura, legumbre, pescado y aceite de oliva como base.",
    ),
    (
        "Volumen limpio",
        "muscle_gain",
        "balanced",
        2750,
        180,
        330,
        80,
        {"breakfast": 20, "lunch": 30, "dinner": 30, "snacks": 20},
        "Superávit moderado con carbohidratos alrededor del entrenamiento.",
    ),
    (
        "Volumen alto en proteínas",
        "muscle_gain",
        "high_protein",
        2700,
        200,
        280,
        85,
        {"breakfast": 25, "lunch": 30, "dinner": 25, "snacks": 20},
        "Cinco tomas con 35–45 g de proteína cada una.",
    ),
    (
        "Mantenimiento equilibrado",
        "maintenance",
        "balanced",
        2150,
        130,
        250,
        70,
        {"breakfast": 20, "lunch": 30, "dinner": 30, "snacks": 20},
        "Reparto equilibrado para mantener el peso con actividad moderada.",
    ),
    (
        "Mantenimiento vegetariano",
        "maintenance",
        "vegetarian",
        2150,
        110,
        270,
        70,
        {"breakfast": 20, "lunch": 35, "dinner": 30, "snacks": 15},
        "Proteína de huevo, lácteos y legumbres.",
    ),
]

# Main demo clients: (email, first_name, last_name, gender, birth_date, status to reach)
MAIN_CLIENTS = [
    ("cliente@entrenanutricion.dev", "Lucía", "Fernández", "F", "1992-04-18", "active"),
    ("pendiente@entrenanutricion.dev", "Jordi", "Puig", "M", "1988-09-02", "pending_assignment"),
    ("nuevo@entrenanutricion.dev", "Sara", "Martín", "F", "1999-12-11", "pending_onboarding"),
]

# Extra clients spread over the previous and the current year for the growth chart.
# (first_name, last_name, gender, year offset (-1 previous, 0 current), month, status to reach)
EXTRA_CLIENTS = [
    ("Pablo", "Romero", "M", -1, 1, "active"),
    ("Marta", "Gil", "F", -1, 2, "active"),
    ("Iván", "Ortega", "M", -1, 3, "active"),
    ("Nuria", "Serra", "F", -1, 5, "pending_assignment"),
    ("Carlos", "Molina", "M", -1, 6, "active"),
    ("Ana", "Castro", "F", -1, 8, "active"),
    ("Pau", "Ferrer", "M", -1, 9, "pending_onboarding"),
    ("Irene", "Navarro", "F", -1, 11, "active"),
    ("Hugo", "Delgado", "M", -1, 12, "active"),
    ("Claudia", "Rubio", "F", 0, 1, "active"),
    ("Àlex", "Costa", "O", 0, 2, "pending_assignment"),
    ("Laia", "Vila", "F", 0, 3, "active"),
    ("Diego", "Herrera", "M", 0, 4, "active"),
    ("Paula", "Iglesias", "F", 0, 5, "active"),
    ("Marc", "Roca", "M", 0, 6, "pending_onboarding"),
    ("Sofía", "Méndez", "F", 0, 7, "active"),
    ("Eric", "Sanz", "M", 0, 8, "pending_assignment"),
    ("Julia", "Prieto", "F", 0, 9, "active"),
]

# Food library (phase 9). Approximate reference values per 100 g (raw unless stated), in the
# order of FOOD_COLUMNS; None = not provided. For demonstration only, not dietary advice.
FOOD_COLUMNS = (
    "calories",
    "proteins_g",
    "carbs_g",
    "fats_g",
    "fiber_g",
    "sugars_g",
    "saturated_fat_g",
    "sodium_mg",
    "potassium_mg",
    "calcium_mg",
    "iron_mg",
    "magnesium_mg",
    "vitamin_a_ug",
    "vitamin_c_mg",
    "vitamin_d_ug",
    "vitamin_b12_ug",
)
# fmt: off
FOODS = [
    # name, category, kcal, prot, carbs, fat, fiber, sugars, sat, Na, K, Ca, Fe, Mg, vitA, vitC, vitD, B12
    ("Pechuga de pollo", "meat", 120, 22.5, 0, 2.6, 0, 0, 0.6, 45, 334, 5, 0.4, 28, 9, 0, 0.1, 0.2),
    ("Ternera magra", "meat", 131, 22.0, 0, 4.6, 0, 0, 1.8, 55, 330, 5, 2.2, 22, 0, 0, 0.1, 1.8),
    ("Salmón", "fish", 208, 20.4, 0, 13.4, 0, 0, 3.1, 59, 363, 9, 0.3, 27, 58, 0, 11.0, 3.2),
    ("Bacalao fresco", "fish", 82, 17.8, 0, 0.7, 0, 0, 0.1, 54, 413, 16, 0.4, 32, 12, 1.0, 0.9, 0.9),
    ("Atún al natural en conserva", "fish", 116, 25.5, 0, 0.8, 0, 0, 0.2, 247, 237, 11, 1.5, 27, 5, 0, 1.7, 2.5),
    ("Huevo", "eggs", 143, 12.6, 0.7, 9.5, 0, 0.4, 3.1, 142, 138, 56, 1.8, 12, 160, 0, 2.0, 0.9),
    ("Leche semidesnatada", "dairy", 50, 3.3, 4.8, 2.0, 0, 4.8, 1.3, 47, 140, 120, 0, 11, 28, 0, None, 0.5),
    ("Yogur natural", "dairy", 61, 3.5, 4.7, 3.3, 0, 4.7, 2.1, 46, 155, 121, 0.1, 12, 27, 0.5, 0.1, 0.4),
    ("Mozzarella", "dairy", 300, 22.2, 2.2, 22.4, 0, 1.0, 13.2, 627, 76, 505, 0.4, 20, 179, 0, 0.4, 2.3),
    ("Arroz blanco (crudo)", "grains", 365, 7.1, 80.0, 0.7, 1.3, 0.1, 0.2, 5, 115, 28, 0.8, 25, 0, 0, 0, 0),
    ("Pasta (cruda)", "grains", 371, 13.0, 75.0, 1.5, 3.2, 2.7, 0.3, 6, 223, 21, 1.3, 53, 0, 0, 0, 0),
    ("Copos de avena", "grains", 389, 16.9, 66.3, 6.9, 10.6, 1.0, 1.2, 2, 429, 54, 4.7, 177, 0, 0, 0, 0),
    ("Pan integral", "grains", 247, 13.0, 41.0, 3.4, 7.0, 6.0, 0.7, 450, 250, 107, 2.5, 75, 0, 0, 0, 0),
    ("Quinoa (cruda)", "grains", 368, 14.1, 64.2, 6.1, 7.0, None, 0.7, 5, 563, 47, 4.6, 197, 1, 0, 0, 0),
    ("Lentejas (secas)", "legumes", 352, 24.6, 63.0, 1.1, 10.7, 2.0, 0.2, 6, 677, 35, 6.5, 47, 2, 4.5, 0, 0),
    ("Garbanzos (secos)", "legumes", 378, 20.5, 63.0, 6.0, 12.2, 10.7, 0.6, 24, 718, 57, 4.3, 79, 3, 4.0, 0, 0),
    ("Tofu firme", "legumes", 144, 17.3, 2.8, 8.7, 2.3, 0.6, 1.3, 14, 237, 683, 2.7, 58, 0, 0.2, 0, 0),
    ("Patata", "vegetables", 77, 2.0, 17.0, 0.1, 2.2, 0.8, 0, 6, 425, 12, 0.8, 23, 0, 19.7, 0, 0),
    ("Brócoli", "vegetables", 34, 2.8, 6.6, 0.4, 2.6, 1.7, 0, 33, 316, 47, 0.7, 21, 31, 89.2, 0, 0),
    ("Espinacas", "vegetables", 23, 2.9, 3.6, 0.4, 2.2, 0.4, 0.1, 79, 558, 99, 2.7, 79, 469, 28.1, 0, 0),
    ("Tomate", "vegetables", 18, 0.9, 3.9, 0.2, 1.2, 2.6, 0, 5, 237, 10, 0.3, 11, 42, 13.7, 0, 0),
    ("Zanahoria", "vegetables", 41, 0.9, 9.6, 0.2, 2.8, 4.7, 0, 69, 320, 33, 0.3, 12, 835, 5.9, 0, 0),
    ("Judías verdes", "vegetables", 31, 1.8, 7.0, 0.2, 2.7, 3.3, 0, 6, 211, 37, 1.0, 25, 35, 12.2, 0, 0),
    ("Plátano", "fruits", 89, 1.1, 22.8, 0.3, 2.6, 12.2, 0.1, 1, 358, 5, 0.3, 27, 3, 8.7, 0, 0),
    ("Manzana", "fruits", 52, 0.3, 13.8, 0.2, 2.4, 10.4, 0, 1, 107, 6, 0.1, 5, 3, 4.6, 0, 0),
    ("Naranja", "fruits", 47, 0.9, 11.8, 0.1, 2.4, 9.4, 0, 0, 181, 40, 0.1, 10, 11, 53.2, 0, 0),
    ("Fresas", "fruits", 32, 0.7, 7.7, 0.3, 2.0, 4.9, 0, 1, 153, 16, 0.4, 13, 1, 58.8, 0, 0),
    ("Aguacate", "fruits", 160, 2.0, 8.5, 14.7, 6.7, 0.7, 2.1, 7, 485, 12, 0.6, 29, 7, 10.0, 0, 0),
    ("Almendras", "nuts_seeds", 579, 21.2, 21.6, 49.9, 12.5, 4.4, 3.8, 1, 733, 269, 3.7, 270, 0, 0, 0, 0),
    ("Nueces", "nuts_seeds", 654, 15.2, 13.7, 65.2, 6.7, 2.6, 6.1, 2, 441, 98, 2.9, 158, 1, 1.3, 0, 0),
    ("Aceite de oliva virgen extra", "fats_oils", 884, 0, 0, 100.0, 0, 0, 13.8, 2, 1, 1, 0.6, 0, 0, 0, 0, 0),
]
# fmt: on

# Logged sets of the demo (phase 12): starting load and increase every two sessions, in kg.
# Exercises not listed are done with the body weight (no load).
DEMO_LOADS = {
    "Press de banca": (40, 2.5),
    "Aperturas con mancuernas": (10, 1),
    "Press francés": (20, 2.5),
    "Extensión de tríceps en polea": (15, 2.5),
    "Remo con barra": (40, 2.5),
    "Jalón al pecho": (35, 2.5),
    "Curl de bíceps con barra": (20, 2.5),
    "Curl martillo": (10, 1),
    "Press militar": (25, 2.5),
    "Elevaciones laterales": (6, 1),
    "Encogimientos con mancuernas": (16, 2),
    "Sentadilla": (50, 2.5),
    "Zancadas": (10, 2),
    "Peso muerto rumano": (50, 2.5),
    "Prensa de piernas": (80, 5),
    "Elevación de gemelos": (40, 2.5),
    "Hip thrust": (50, 5),
}
DEMO_LOAD_STEPS = 12  # the load stops growing after 12 increases

# Notes with the team (phase 12): (author, days ago, read by the other side, text).
DEMO_NOTES = [
    (
        "trainer",
        6,
        True,
        "¡Buen comienzo de semana! Si la sentadilla te resulta fácil, sube 2,5 kg en la próxima "
        "sesión.",
    ),
    ("client", 5, True, "Gracias. El jueves noté algo de carga en la rodilla, ¿lo hago igual?"),
    (
        "trainer",
        5,
        True,
        "Baja un poco la profundidad y cuida que la rodilla siga la punta del pie. Si molesta, "
        "cámbiala por prensa.",
    ),
    (
        "nutritionist",
        1,
        False,
        "Vas muy bien con el peso. Recuerda la proteína en la cena los días de entreno.",
    ),
]
# Unread notes of other demo clients, so the staff inbox is not empty.
DEMO_INBOX_NOTES = [
    "¿Puedo cambiar el entreno del viernes al sábado esta semana?",
    "No encuentro quinoa en mi supermercado, ¿por qué la sustituyo?",
]

# Sample day menus (phase 13) by plan category: (meal, food, grams). The seed scales the grams to
# the calories of each plan (multiples of 5 g).
OIL = "Aceite de oliva virgen extra"
DEMO_MENUS = {
    "weight_loss": [
        ("breakfast", "Copos de avena", 50),
        ("breakfast", "Leche semidesnatada", 250),
        ("breakfast", "Fresas", 150),
        ("lunch", "Pechuga de pollo", 150),
        ("lunch", "Arroz blanco (crudo)", 70),
        ("lunch", "Brócoli", 200),
        ("lunch", OIL, 10),
        ("dinner", "Salmón", 130),
        ("dinner", "Patata", 200),
        ("dinner", "Judías verdes", 200),
        ("dinner", OIL, 10),
        ("snacks", "Yogur natural", 125),
        ("snacks", "Manzana", 150),
        ("snacks", "Almendras", 20),
    ],
    "muscle_gain": [
        ("breakfast", "Copos de avena", 90),
        ("breakfast", "Leche semidesnatada", 300),
        ("breakfast", "Plátano", 120),
        ("breakfast", "Huevo", 120),
        ("lunch", "Ternera magra", 180),
        ("lunch", "Pasta (cruda)", 120),
        ("lunch", "Tomate", 150),
        ("lunch", OIL, 15),
        ("dinner", "Pechuga de pollo", 180),
        ("dinner", "Quinoa (cruda)", 90),
        ("dinner", "Espinacas", 150),
        ("dinner", OIL, 15),
        ("snacks", "Yogur natural", 250),
        ("snacks", "Nueces", 30),
        ("snacks", "Pan integral", 60),
        ("snacks", "Atún al natural en conserva", 80),
    ],
    "maintenance": [
        ("breakfast", "Pan integral", 80),
        ("breakfast", "Tomate", 100),
        ("breakfast", OIL, 10),
        ("breakfast", "Naranja", 200),
        ("lunch", "Lentejas (secas)", 80),
        ("lunch", "Zanahoria", 100),
        ("lunch", "Bacalao fresco", 150),
        ("lunch", OIL, 10),
        ("dinner", "Tofu firme", 150),
        ("dinner", "Arroz blanco (crudo)", 70),
        ("dinner", "Brócoli", 150),
        ("dinner", OIL, 10),
        ("snacks", "Yogur natural", 125),
        ("snacks", "Plátano", 120),
        ("snacks", "Almendras", 20),
    ],
}
DEMO_FOOD_LOG_DAYS = 6  # the demo client logged the last six days (not today)
