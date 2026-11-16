"""English and Catalan texts of the demo catalog (phase 14), keyed by the Spanish name.

Exercises: name, description, steps, technique, common mistakes and benefits. Workouts, training
plans and nutrition plans: name and description. Foods: name.
"""

EXERCISES = {
    "Press de banca": {
        "en": {
            "name": "Bench press",
            "description": "Horizontal barbell press lying on a flat bench.",
            "steps": [
                "Lie down with your eyes under the bar and your feet firmly on the floor.",
                "Grip the bar slightly wider than your shoulders and lower it to your chest.",
                "Press until your elbows are straight without locking them.",
            ],
            "technique": "Shoulder blades pulled back, slight lower-back arch and elbows about 45° from the torso.",
            "common_mistakes": "Bouncing the bar off the chest and lifting the glutes off the bench.",
            "benefits": "Builds strength and size in the chest, front deltoids and triceps.",
        },
        "ca": {
            "name": "Press de banca",
            "description": "Empenta horitzontal amb barra estirat en un banc pla.",
            "steps": [
                "Estira't amb els ulls sota la barra i els peus ferms a terra.",
                "Agafa la barra una mica més oberta que les espatlles i baixa-la al pit.",
                "Empeny fins a estendre els colzes sense bloquejar-los.",
            ],
            "technique": "Omòplats retrets, lleuger arc lumbar i colzes a uns 45° del tors.",
            "common_mistakes": "Fer rebotar la barra al pit i aixecar els glutis del banc.",
            "benefits": "Desenvolupa la força i el volum del pectoral, el deltoide anterior i el tríceps.",
        },
    },
    "Flexiones": {
        "en": {
            "name": "Push-ups",
            "description": "Bodyweight press from the floor.",
            "steps": [
                "Place your hands shoulder-width apart and straighten your body.",
                "Lower your chest until it almost touches the floor.",
                "Push the floor away to come back up.",
            ],
            "technique": "Body in a straight line from head to heels, core engaged.",
            "common_mistakes": "Letting the hips sag or flaring the elbows too much.",
            "benefits": "Pushing strength without equipment and core stability.",
        },
        "ca": {
            "name": "Flexions",
            "description": "Empenta amb el pes corporal des de terra.",
            "steps": [
                "Recolza les mans a l'amplada de les espatlles i estira el cos.",
                "Baixa el pit fins gairebé tocar a terra.",
                "Empeny el terra per tornar a dalt.",
            ],
            "technique": "Cos en línia recta del cap als talons, abdomen actiu.",
            "common_mistakes": "Enfonsar el maluc o obrir massa els colzes.",
            "benefits": "Força d'empenta sense material i estabilitat del tronc.",
        },
    },
    "Aperturas con mancuernas": {
        "en": {
            "name": "Dumbbell flyes",
            "description": "Chest isolation on a flat bench.",
            "steps": [
                "Lie down with the dumbbells over your chest and your elbows slightly bent.",
                "Open your arms in an arc until you feel a stretch in the chest.",
                "Close the arc until the dumbbells meet.",
            ],
            "technique": "Keep the same elbow angle throughout the movement.",
            "common_mistakes": "Turning the movement into a press or going too low.",
            "benefits": "Improves range of motion and the mind-muscle connection with the chest.",
        },
        "ca": {
            "name": "Obertures amb manuelles",
            "description": "Aïllament del pectoral en banc pla.",
            "steps": [
                "Estira't amb les manuelles sobre el pit i els colzes lleugerament flexionats.",
                "Obre els braços en arc fins a notar estirament al pit.",
                "Tanca l'arc fins a ajuntar les manuelles.",
            ],
            "technique": "Mantén el mateix angle de colze durant tot el recorregut.",
            "common_mistakes": "Convertir el moviment en un press o baixar massa.",
            "benefits": "Millora el rang de moviment i la connexió amb el pectoral.",
        },
    },
    "Fondos en paralelas": {
        "en": {
            "name": "Parallel bar dips",
            "description": "Vertical bodyweight press.",
            "steps": [
                "Hold yourself on the parallel bars with your arms straight.",
                "Bend your elbows until your shoulders are level with your elbows.",
                "Press until your arms are straight.",
            ],
            "technique": "Torso slightly leaning forward and shoulders away from the ears.",
            "common_mistakes": "Going too low and straining the shoulder.",
            "benefits": "Strong triceps and lower chest with little equipment.",
        },
        "ca": {
            "name": "Fons en paral·leles",
            "description": "Empenta vertical amb el pes corporal.",
            "steps": [
                "Subjecta't a les paral·leles amb els braços estesos.",
                "Flexiona els colzes fins que les espatlles quedin a l'altura dels colzes.",
                "Empeny fins a estendre els braços.",
            ],
            "technique": "Tors lleugerament inclinat i espatlles lluny de les orelles.",
            "common_mistakes": "Baixar massa i forçar l'espatlla.",
            "benefits": "Tríceps i pectoral inferior forts amb poc material.",
        },
    },
    "Press francés": {
        "en": {
            "name": "Skull crushers",
            "description": "Lying elbow extension with an EZ bar.",
            "steps": [
                "Lie down with the bar over your forehead and your arms vertical.",
                "Bend your elbows bringing the bar towards your forehead.",
                "Straighten your elbows to come back up.",
            ],
            "technique": "Elbows fixed and pointing at the ceiling.",
            "common_mistakes": "Flaring the elbows or moving the shoulders.",
            "benefits": "Works the long head of the triceps.",
        },
        "ca": {
            "name": "Press francès",
            "description": "Extensió de colzes estirat amb barra Z.",
            "steps": [
                "Estira't amb la barra sobre el front i els braços verticals.",
                "Flexiona els colzes portant la barra cap al front.",
                "Estén els colzes per tornar a dalt.",
            ],
            "technique": "Colzes fixos i apuntant al sostre.",
            "common_mistakes": "Obrir els colzes o moure les espatlles.",
            "benefits": "Treballa el cap llarg del tríceps.",
        },
    },
    "Extensión de tríceps en polea": {
        "en": {
            "name": "Cable triceps pushdown",
            "description": "Standing elbow extension on a high pulley.",
            "steps": [
                "Grab the rope with your elbows tucked against your body.",
                "Straighten your elbows, pulling the rope apart at the end.",
                "Slowly return to the starting position.",
            ],
            "technique": "Only the forearms move.",
            "common_mistakes": "Leaning the body to move more weight.",
            "benefits": "Safe triceps isolation.",
        },
        "ca": {
            "name": "Extensió de tríceps a la politja",
            "description": "Extensió de colzes dempeus a la politja alta.",
            "steps": [
                "Agafa la corda amb els colzes enganxats al cos.",
                "Estén els colzes separant la corda al final.",
                "Torna a poc a poc a la posició inicial.",
            ],
            "technique": "Només es mouen els avantbraços.",
            "common_mistakes": "Inclinar el cos per moure més pes.",
            "benefits": "Aïllament segur del tríceps.",
        },
    },
    "Dominadas": {
        "en": {
            "name": "Pull-ups",
            "description": "Vertical pull hanging from a bar.",
            "steps": [
                "Hang with an overhand grip slightly wider than your shoulders.",
                "Pull your elbows down until your chin passes the bar.",
                "Lower yourself under control until your arms are straight.",
            ],
            "technique": "Start the movement by pulling the shoulder blades down.",
            "common_mistakes": "Swinging or doing half repetitions.",
            "benefits": "A wide, strong back; a great relative-strength exercise.",
        },
        "ca": {
            "name": "Dominades",
            "description": "Tracció vertical penjat d'una barra.",
            "steps": [
                "Penja't amb presa prona una mica més ampla que les espatlles.",
                "Estira els colzes cap avall fins a passar la barbeta de la barra.",
                "Baixa controlant fins a estendre els braços.",
            ],
            "technique": "Inicia el moviment baixant els omòplats.",
            "common_mistakes": "Balancejar-se o fer mig recorregut.",
            "benefits": "Esquena ampla i forta; gran exercici de força relativa.",
        },
    },
    "Remo con barra": {
        "en": {
            "name": "Barbell row",
            "description": "Horizontal pull with the torso bent forward.",
            "steps": [
                "Bend your torso to about 45° with a neutral back.",
                "Pull the bar towards your navel.",
                "Lower the bar under control.",
            ],
            "technique": "Neutral back and braced core throughout the movement.",
            "common_mistakes": "Rounding the back or pulling with momentum.",
            "benefits": "Back thickness and postural health.",
        },
        "ca": {
            "name": "Rem amb barra",
            "description": "Tracció horitzontal amb el tors inclinat.",
            "steps": [
                "Inclina el tors uns 45° amb l'esquena neutra.",
                "Estira la barra cap al melic.",
                "Baixa la barra amb control.",
            ],
            "technique": "Esquena neutra i abdomen ferm durant tot el moviment.",
            "common_mistakes": "Arrodonir l'esquena o estirar amb impuls.",
            "benefits": "Gruix d'esquena i salut postural.",
        },
    },
    "Jalón al pecho": {
        "en": {
            "name": "Lat pulldown",
            "description": "Vertical pull on a high pulley.",
            "steps": [
                "Sit with your thighs under the pads and grab the bar.",
                "Pull the bar down to your upper chest.",
                "Go back up under control until your arms are straight.",
            ],
            "technique": "Chest up and elbows down and back.",
            "common_mistakes": "Pulling behind the neck or leaning too far back.",
            "benefits": "A progressive alternative to pull-ups.",
        },
        "ca": {
            "name": "Estirada al pit",
            "description": "Tracció vertical a la politja alta.",
            "steps": [
                "Seu amb les cuixes sota els corrons i agafa la barra.",
                "Estira la barra fins a la part alta del pit.",
                "Puja controlant fins a estirar els braços.",
            ],
            "technique": "Pit alt i colzes cap avall i enrere.",
            "common_mistakes": "Estirar per darrere del clatell o tirar-se molt enrere.",
            "benefits": "Alternativa progressiva a les dominades.",
        },
    },
    "Curl de bíceps con barra": {
        "en": {
            "name": "Barbell biceps curl",
            "description": "Standing elbow flexion with a barbell.",
            "steps": [
                "Hold the bar with an underhand grip at shoulder width.",
                "Bend your elbows without moving them away from your sides.",
                "Lower slowly until your arms are straight.",
            ],
            "technique": "Elbows fixed and wrists neutral.",
            "common_mistakes": "Swinging the body to lift the bar.",
            "benefits": "Biceps strength and size.",
        },
        "ca": {
            "name": "Curl de bíceps amb barra",
            "description": "Flexió de colzes dempeus amb barra.",
            "steps": [
                "Agafa la barra amb presa supina a l'amplada de les espatlles.",
                "Flexiona els colzes sense moure'ls dels costats.",
                "Baixa a poc a poc fins a estendre els braços.",
            ],
            "technique": "Colzes fixos i canells neutres.",
            "common_mistakes": "Balancejar el cos per pujar la barra.",
            "benefits": "Força i volum del bíceps.",
        },
    },
    "Curl martillo": {
        "en": {
            "name": "Hammer curl",
            "description": "Elbow flexion with a neutral grip.",
            "steps": [
                "Hold the dumbbells with your palms facing each other.",
                "Bend your elbows, alternating or both at once.",
                "Lower under control.",
            ],
            "technique": "Keep the neutral grip throughout the movement.",
            "common_mistakes": "Using momentum from the back.",
            "benefits": "Works the brachialis and the forearm.",
        },
        "ca": {
            "name": "Curl martell",
            "description": "Flexió de colzes amb presa neutra.",
            "steps": [
                "Agafa les manuelles amb els palmells encarats.",
                "Flexiona els colzes alternant o alhora.",
                "Baixa amb control.",
            ],
            "technique": "Mantén la presa neutra tot el recorregut.",
            "common_mistakes": "Fer servir l'impuls de l'esquena.",
            "benefits": "Treballa el braquial i l'avantbraç.",
        },
    },
    "Press militar": {
        "en": {
            "name": "Overhead press",
            "description": "Standing vertical barbell press.",
            "steps": [
                "Hold the bar at collarbone height.",
                "Press the bar overhead.",
                "Lower it to your collarbones under control.",
            ],
            "technique": "Glutes and core tight so the back does not arch.",
            "common_mistakes": "Overarching the lower back.",
            "benefits": "Strong shoulders and core stability.",
        },
        "ca": {
            "name": "Press militar",
            "description": "Empenta vertical dempeus amb barra.",
            "steps": [
                "Col·loca la barra a l'altura de les clavícules.",
                "Empeny la barra per sobre del cap.",
                "Baixa fins a les clavícules amb control.",
            ],
            "technique": "Glutis i abdomen contrets per no arquejar l'esquena.",
            "common_mistakes": "Hiperestendre la zona lumbar.",
            "benefits": "Espatlles fortes i estabilitat del tronc.",
        },
    },
    "Elevaciones laterales": {
        "en": {
            "name": "Lateral raises",
            "description": "Side deltoid isolation with dumbbells.",
            "steps": [
                "Standing, dumbbells at your sides and elbows slightly bent.",
                "Raise your arms to shoulder height.",
                "Lower slowly.",
            ],
            "technique": "Lead the movement with your elbows, not your hands.",
            "common_mistakes": "Going above shoulder height or using momentum.",
            "benefits": "Wider, more balanced shoulders.",
        },
        "ca": {
            "name": "Elevacions laterals",
            "description": "Aïllament del deltoide lateral amb manuelles.",
            "steps": [
                "Dempeus, manuelles als costats i colzes una mica flexionats.",
                "Eleva els braços fins a l'altura de les espatlles.",
                "Baixa a poc a poc.",
            ],
            "technique": "Lidera el moviment amb els colzes, no amb les mans.",
            "common_mistakes": "Pujar per sobre de les espatlles o amb impuls.",
            "benefits": "Espatlles més amples i equilibrades.",
        },
    },
    "Encogimientos con mancuernas": {
        "en": {
            "name": "Dumbbell shrugs",
            "description": "Loaded shoulder elevation.",
            "steps": [
                "Standing, hold the dumbbells at your sides.",
                "Raise your shoulders towards your ears.",
                "Hold for a second at the top and lower.",
            ],
            "technique": "Vertical movement, without rolling the shoulders.",
            "common_mistakes": "Moving the head forward.",
            "benefits": "Strong upper trapezius.",
        },
        "ca": {
            "name": "Encongiments amb manuelles",
            "description": "Elevació d'espatlles amb càrrega.",
            "steps": [
                "Dempeus, agafa les manuelles als costats.",
                "Eleva les espatlles cap a les orelles.",
                "Mantén un segon a dalt i baixa.",
            ],
            "technique": "Moviment vertical, sense rotar les espatlles.",
            "common_mistakes": "Moure el cap cap endavant.",
            "benefits": "Trapezi superior fort.",
        },
    },
    "Sentadilla": {
        "en": {
            "name": "Squat",
            "description": "Knee and hip bend with a barbell on the back.",
            "steps": [
                "Place the bar on your upper back and your feet shoulder-width apart.",
                "Go down bending knees and hips until you break parallel.",
                "Push the floor away to stand up.",
            ],
            "technique": "Knees in line with the toes and a neutral back.",
            "common_mistakes": "Lifting the heels or letting the knees cave in.",
            "benefits": "Overall lower-body strength.",
        },
        "ca": {
            "name": "Esquat",
            "description": "Flexió de genolls i maluc amb barra a l'esquena.",
            "steps": [
                "Col·loca la barra sobre els trapezis i els peus a l'amplada de les espatlles.",
                "Baixa flexionant genolls i maluc fins a trencar el paral·lel.",
                "Empeny el terra per pujar.",
            ],
            "technique": "Genolls en la direcció de les puntes dels peus i esquena neutra.",
            "common_mistakes": "Aixecar els talons o ajuntar els genolls.",
            "benefits": "Força global del tren inferior.",
        },
    },
    "Zancadas": {
        "en": {
            "name": "Lunges",
            "description": "Stepping with both knees bent.",
            "steps": [
                "Take a long step forward.",
                "Go down until the back knee almost touches the floor.",
                "Push with the front leg to come back.",
            ],
            "technique": "Upright torso and a stable front knee.",
            "common_mistakes": "Short steps that load the knee.",
            "benefits": "Single-leg strength and balance.",
        },
        "ca": {
            "name": "Gambades",
            "description": "Desplaçament amb flexió de tots dos genolls.",
            "steps": [
                "Fes una passa llarga cap endavant.",
                "Baixa fins que el genoll del darrere gairebé toqui a terra.",
                "Empeny amb la cama del davant per tornar.",
            ],
            "technique": "Tors dret i genoll del davant estable.",
            "common_mistakes": "Passes curtes que carreguen el genoll.",
            "benefits": "Força unilateral i equilibri.",
        },
    },
    "Peso muerto rumano": {
        "en": {
            "name": "Romanian deadlift",
            "description": "Hip hinge with a barbell.",
            "steps": [
                "Standing, bar in front of your thighs and knees slightly bent.",
                "Push your hips back, lowering the bar close to your legs.",
                "Come back up driving your hips forward.",
            ],
            "technique": "Neutral back and the bar always close to the body.",
            "common_mistakes": "Rounding the back or bending the knees too much.",
            "benefits": "Strong hamstrings and glutes, a better hip hinge.",
        },
        "ca": {
            "name": "Pes mort romanès",
            "description": "Frontissa de maluc amb barra.",
            "steps": [
                "Dempeus, barra davant de les cuixes i genolls lleugerament flexionats.",
                "Porta el maluc enrere baixant la barra enganxada a les cames.",
                "Torna empenyent el maluc cap endavant.",
            ],
            "technique": "Esquena neutra i barra sempre a prop del cos.",
            "common_mistakes": "Arrodonir l'esquena o flexionar massa els genolls.",
            "benefits": "Isquiotibials i glutis forts, millor frontissa de maluc.",
        },
    },
    "Prensa de piernas": {
        "en": {
            "name": "Leg press",
            "description": "Machine leg press.",
            "steps": [
                "Sit down and place your feet on the platform.",
                "Lower the platform by bending your knees.",
                "Push without locking your knees.",
            ],
            "technique": "Lower back always against the backrest.",
            "common_mistakes": "Going so low that the pelvis comes off the seat.",
            "benefits": "Quadriceps size with low technical demand.",
        },
        "ca": {
            "name": "Premsa de cames",
            "description": "Empenta de cames a màquina.",
            "steps": [
                "Seu i recolza els peus a la plataforma.",
                "Baixa la plataforma flexionant els genolls.",
                "Empeny sense bloquejar els genolls.",
            ],
            "technique": "Zona lumbar sempre recolzada al respatller.",
            "common_mistakes": "Baixar tant que la pelvis es desenganxi.",
            "benefits": "Volum de quàdriceps amb poca exigència tècnica.",
        },
    },
    "Elevación de gemelos": {
        "en": {
            "name": "Calf raises",
            "description": "Standing ankle extension.",
            "steps": [
                "Place the balls of your feet on a step.",
                "Rise onto your toes as high as possible.",
                "Lower until you feel a stretch.",
            ],
            "technique": "Full range of motion and a pause at the top.",
            "common_mistakes": "Bouncing at the bottom.",
            "benefits": "Strong calves and stable ankles.",
        },
        "ca": {
            "name": "Elevació de bessons",
            "description": "Extensió de turmells dempeus.",
            "steps": [
                "Recolza la punta dels peus en un esglaó.",
                "Puja sobre les puntes tan amunt com puguis.",
                "Baixa fins a notar estirament.",
            ],
            "technique": "Recorregut complet i pausa a dalt.",
            "common_mistakes": "Fer rebots a la part baixa.",
            "benefits": "Bessons forts i turmells estables.",
        },
    },
    "Hip thrust": {
        "en": {
            "name": "Hip thrust",
            "description": "Hip extension with the back resting on a bench.",
            "steps": [
                "Rest your upper back on the bench and the bar on your hips.",
                "Drive your hips up until knees, hips and shoulders are aligned.",
                "Lower your hips under control.",
            ],
            "technique": "Chin tucked and pelvis tilted back at the top.",
            "common_mistakes": "Arching the lower back instead of extending the hips.",
            "benefits": "The most direct exercise for the gluteus maximus.",
        },
        "ca": {
            "name": "Hip thrust",
            "description": "Extensió de maluc amb l'esquena recolzada en un banc.",
            "steps": [
                "Recolza la part alta de l'esquena al banc i la barra al maluc.",
                "Empeny el maluc cap amunt fins a alinear genolls, maluc i espatlles.",
                "Baixa el maluc amb control.",
            ],
            "technique": "Barbeta recollida i pelvis en retroversió a dalt.",
            "common_mistakes": "Arquejar la zona lumbar en lloc d'estendre el maluc.",
            "benefits": "L'exercici més directe per al gluti major.",
        },
    },
    "Plancha": {
        "en": {
            "name": "Plank",
            "description": "Core isometric hold on the forearms.",
            "steps": [
                "Rest on your forearms and the tips of your toes.",
                "Line up your head, hips and heels.",
                "Hold the position breathing normally.",
            ],
            "technique": "Core and glutes engaged; do not let the hips sag.",
            "common_mistakes": "Raising the hips too high or holding your breath.",
            "benefits": "Core stability and lower-back protection.",
        },
        "ca": {
            "name": "Planxa",
            "description": "Isometria de tronc sobre els avantbraços.",
            "steps": [
                "Recolza els avantbraços i les puntes dels peus.",
                "Alinea cap, maluc i talons.",
                "Mantén la posició respirant amb normalitat.",
            ],
            "technique": "Abdomen i glutis actius; no enfonsis el maluc.",
            "common_mistakes": "Elevar massa el maluc o aguantar la respiració.",
            "benefits": "Estabilitat del core i protecció lumbar.",
        },
    },
    "Crunch abdominal": {
        "en": {
            "name": "Crunch",
            "description": "Lying trunk flexion.",
            "steps": [
                "Lie down with your knees bent and your hands beside your temples.",
                "Lift your shoulders off the floor by contracting your abs.",
                "Lower slowly.",
            ],
            "technique": "Move the trunk, do not pull on your neck.",
            "common_mistakes": "Using the arms for momentum.",
            "benefits": "Strengthens the rectus abdominis.",
        },
        "ca": {
            "name": "Crunch abdominal",
            "description": "Flexió de tronc estirat.",
            "steps": [
                "Estira't amb els genolls flexionats i les mans al costat de les temples.",
                "Eleva les espatlles de terra contraient l'abdomen.",
                "Baixa a poc a poc.",
            ],
            "technique": "Mou el tronc, no estiris del coll.",
            "common_mistakes": "Impulsar-se amb els braços.",
            "benefits": "Enforteix el recte abdominal.",
        },
    },
    "Elevación de piernas colgado": {
        "en": {
            "name": "Hanging leg raise",
            "description": "Hip flexion hanging from a bar.",
            "steps": [
                "Hang from the bar with your arms straight.",
                "Raise your legs to horizontal.",
                "Lower without swinging.",
            ],
            "technique": "Control the swing by engaging your abs.",
            "common_mistakes": "Using leg momentum.",
            "benefits": "Lower abs and grip strength.",
        },
        "ca": {
            "name": "Elevació de cames penjat",
            "description": "Flexió de maluc penjat d'una barra.",
            "steps": [
                "Penja't de la barra amb els braços estesos.",
                "Eleva les cames fins a l'horitzontal.",
                "Baixa sense balancejar-te.",
            ],
            "technique": "Controla el balanceig activant l'abdomen.",
            "common_mistakes": "Fer servir l'impuls de les cames.",
            "benefits": "Abdomen inferior i força de presa.",
        },
    },
    "Hiperextensiones lumbares": {
        "en": {
            "name": "Back extensions",
            "description": "Trunk extension on a Roman chair.",
            "steps": [
                "Get on the bench with your hips at the edge of the pad.",
                "Lower your trunk with a neutral back.",
                "Come up until your trunk is in line with your legs.",
            ],
            "technique": "Do not go past the line of the body when coming up.",
            "common_mistakes": "Overextending the spine at the top.",
            "benefits": "A resilient lower back.",
        },
        "ca": {
            "name": "Hiperextensions lumbars",
            "description": "Extensió de tronc en banc romà.",
            "steps": [
                "Col·loca't al banc amb el maluc a la vora del suport.",
                "Baixa el tronc amb l'esquena neutra.",
                "Puja fins a alinear el tronc amb les cames.",
            ],
            "technique": "No sobrepassis la línia del cos en pujar.",
            "common_mistakes": "Hiperestendre la columna a dalt.",
            "benefits": "Zona lumbar resistent.",
        },
    },
    "Burpees": {
        "en": {
            "name": "Burpees",
            "description": "Full-body metabolic exercise.",
            "steps": [
                "From standing, put your hands down and jump your feet back.",
                "Do a push-up and bring your feet in.",
                "Jump with your arms overhead.",
            ],
            "technique": "Keep the pace without losing alignment in the plank.",
            "common_mistakes": "Letting the hips sag when jumping back.",
            "benefits": "Improves cardiovascular fitness and power.",
        },
        "ca": {
            "name": "Burpees",
            "description": "Exercici metabòlic de cos complet.",
            "steps": [
                "Des de dempeus, recolza les mans i porta els peus enrere.",
                "Fes una flexió i recull els peus.",
                "Salta amb els braços amunt.",
            ],
            "technique": "Mantén el ritme sense perdre l'alineació a la planxa.",
            "common_mistakes": "Enfonsar el maluc en saltar enrere.",
            "benefits": "Millora la condició cardiovascular i la potència.",
        },
    },
}

WORKOUTS = {
    "Core": {
        "en": {"name": "Core", "description": "Trunk stability and strength."},
        "ca": {"name": "Core", "description": "Estabilitat i força del tronc."},
    },
    "Piernas": {
        "en": {"name": "Legs", "description": "Complete lower body."},
        "ca": {"name": "Cames", "description": "Tren inferior complet."},
    },
    "Espalda y bíceps": {
        "en": {"name": "Back and biceps", "description": "Pulls and elbow flexors."},
        "ca": {"name": "Esquena i bíceps", "description": "Traccions i flexors del colze."},
    },
    "Pecho y tríceps": {
        "en": {
            "name": "Chest and triceps",
            "description": "Horizontal presses and elbow extension.",
        },
        "ca": {
            "name": "Pit i tríceps",
            "description": "Empentes horitzontals i extensió de colzes.",
        },
    },
    "Hombro": {
        "en": {"name": "Shoulders", "description": "Deltoids and trapezius."},
        "ca": {"name": "Espatlla", "description": "Deltoides i trapezi."},
    },
    "Full body": {
        "en": {"name": "Full body", "description": "Full-body session."},
        "ca": {"name": "Full body", "description": "Sessió de cos complet."},
    },
}

TRAINING_PLANS = {
    "Iniciación full body": {
        "en": {
            "name": "Full body for beginners",
            "description": "Three weekly sessions to build the habit and learn the basic technique.",
        },
        "ca": {
            "name": "Iniciació full body",
            "description": "Tres sessions setmanals per crear l'hàbit i aprendre la tècnica bàsica.",
        },
    },
    "Hipertrofia 4 días": {
        "en": {
            "name": "Hypertrophy 4 days",
            "description": "Split routine by muscle groups to gain muscle mass.",
        },
        "ca": {
            "name": "Hipertròfia 4 dies",
            "description": "Rutina dividida per grups musculars per guanyar massa muscular.",
        },
    },
    "Quema grasa 3 días": {
        "en": {
            "name": "Fat burn 3 days",
            "description": "Metabolic and strength sessions to lose fat while keeping muscle.",
        },
        "ca": {
            "name": "Crema greix 3 dies",
            "description": "Sessions metabòliques i de força per perdre greix conservant múscul.",
        },
    },
}

MEAL_PLANS = {
    "Déficit moderado alto en proteínas": {
        "en": {
            "name": "Moderate high-protein deficit",
            "description": "A deficit of about 400 kcal with high protein to preserve muscle mass.",
        },
        "ca": {
            "name": "Dèficit moderat alt en proteïnes",
            "description": "Dèficit d'unes 400 kcal amb proteïna alta per preservar la massa muscular.",
        },
    },
    "Déficit mediterráneo": {
        "en": {
            "name": "Mediterranean deficit",
            "description": "Vegetables, legumes, fish and olive oil as the base.",
        },
        "ca": {
            "name": "Dèficit mediterrani",
            "description": "Verdura, llegum, peix i oli d'oliva com a base.",
        },
    },
    "Volumen limpio": {
        "en": {
            "name": "Lean bulk",
            "description": "A moderate surplus with carbohydrates around training.",
        },
        "ca": {
            "name": "Volum net",
            "description": "Superàvit moderat amb hidrats de carboni al voltant de l'entrenament.",
        },
    },
    "Volumen alto en proteínas": {
        "en": {
            "name": "High-protein bulk",
            "description": "Five meals with 35–45 g of protein each.",
        },
        "ca": {
            "name": "Volum alt en proteïnes",
            "description": "Cinc preses amb 35–45 g de proteïna cadascuna.",
        },
    },
    "Mantenimiento equilibrado": {
        "en": {
            "name": "Balanced maintenance",
            "description": "A balanced split to keep the weight with moderate activity.",
        },
        "ca": {
            "name": "Manteniment equilibrat",
            "description": "Repartiment equilibrat per mantenir el pes amb activitat moderada.",
        },
    },
    "Mantenimiento vegetariano": {
        "en": {
            "name": "Vegetarian maintenance",
            "description": "Protein from eggs, dairy and legumes.",
        },
        "ca": {
            "name": "Manteniment vegetarià",
            "description": "Proteïna d'ou, làctics i llegums.",
        },
    },
}

FOODS = {
    "Pechuga de pollo": {"en": "Chicken breast", "ca": "Pit de pollastre"},
    "Ternera magra": {"en": "Lean beef", "ca": "Vedella magra"},
    "Salmón": {"en": "Salmon", "ca": "Salmó"},
    "Bacalao fresco": {"en": "Fresh cod", "ca": "Bacallà fresc"},
    "Atún al natural en conserva": {
        "en": "Canned tuna in water",
        "ca": "Tonyina al natural en conserva",
    },
    "Huevo": {"en": "Egg", "ca": "Ou"},
    "Leche semidesnatada": {"en": "Semi-skimmed milk", "ca": "Llet semidesnatada"},
    "Yogur natural": {"en": "Plain yogurt", "ca": "Iogurt natural"},
    "Mozzarella": {"en": "Mozzarella", "ca": "Mozzarella"},
    "Arroz blanco (crudo)": {"en": "White rice (raw)", "ca": "Arròs blanc (cru)"},
    "Pasta (cruda)": {"en": "Pasta (raw)", "ca": "Pasta (crua)"},
    "Copos de avena": {"en": "Rolled oats", "ca": "Flocs de civada"},
    "Pan integral": {"en": "Wholemeal bread", "ca": "Pa integral"},
    "Quinoa (cruda)": {"en": "Quinoa (raw)", "ca": "Quinoa (crua)"},
    "Lentejas (secas)": {"en": "Lentils (dry)", "ca": "Llenties (seques)"},
    "Garbanzos (secos)": {"en": "Chickpeas (dry)", "ca": "Cigrons (secs)"},
    "Tofu firme": {"en": "Firm tofu", "ca": "Tofu ferm"},
    "Patata": {"en": "Potato", "ca": "Patata"},
    "Brócoli": {"en": "Broccoli", "ca": "Bròquil"},
    "Espinacas": {"en": "Spinach", "ca": "Espinacs"},
    "Tomate": {"en": "Tomato", "ca": "Tomàquet"},
    "Zanahoria": {"en": "Carrot", "ca": "Pastanaga"},
    "Judías verdes": {"en": "Green beans", "ca": "Mongetes tendres"},
    "Plátano": {"en": "Banana", "ca": "Plàtan"},
    "Manzana": {"en": "Apple", "ca": "Poma"},
    "Naranja": {"en": "Orange", "ca": "Taronja"},
    "Fresas": {"en": "Strawberries", "ca": "Maduixes"},
    "Aguacate": {"en": "Avocado", "ca": "Alvocat"},
    "Almendras": {"en": "Almonds", "ca": "Ametlles"},
    "Nueces": {"en": "Walnuts", "ca": "Nous"},
    "Aceite de oliva virgen extra": {
        "en": "Extra virgin olive oil",
        "ca": "Oli d'oliva verge extra",
    },
}
