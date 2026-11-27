# Бункер A: промпты (реалистичный 3D-фон + 2D-персонажи)

Правило стиля: фон фотореалистичный 3D, персонажи 2D с жирным контуром, простым лицом, реалистичной одеждой; мимика меняется по сцене. Фоны и персонажи генерируются **отдельно**: фон без людей, каждый персонаж отдельной картинкой на прозрачном фоне. Я накладываю персонажей на фон и двигаю их (шаг, лестница, смена выражения).

Формат: фоны 9:16; персонажи PNG с прозрачным фоном, в полный рост. Текста нигде нет.
Чтобы персонаж был одинаковым, приложи к каждой следующей генерации первую удачную картинку этого персонажа как образец.

## Общие блоки

**ФОН (вставлять в каждый фон):**
photorealistic 3D render, cinematic lighting, realistic detailed textures, shallow depth of field, Unreal Engine look, empty scene, no people, vertical 9:16, no text, no letters

**ПЕРСОНАЖ (вставлять в каждого персонажа):**
2D cartoon character, bold thick black outlines, flat cel shading, simple face with dot eyes and simple eyebrows and mouth, realistic detailed clothing with fabric folds, seams, zippers and wear, full body, transparent background, no text

**БУНКЕР:**
small underground bunker under a village garage, concrete panel walls with bolts, ventilation duct and cables along the ceiling, metal shelves with canned food and boxes, fire extinguisher, round steel hatch in the ceiling with a vertical metal ladder down to the floor, caged lamp with warm light

## Фоны (7 штук, без людей)

- **Ф1. Под люком.** Low angle from the bunker floor looking up at the round steel ceiling hatch and the vertical ladder, warm caged lamp, dust in the air. + ФОН + БУНКЕР
- **Ф2. Главная комната.** Wide view of the bunker room with a long empty wooden bench along the wall under the lamp, shelves with canned food, ladder to the ceiling hatch on the right. + ФОН + БУНКЕР
- **Ф3. Запасы.** The bunker technical corner: a blue water tank with a pipe from a well, a ventilation filter unit with a hand crank, a door to a small generator room with an exhaust pipe through the wall. + ФОН + БУНКЕР
- **Ф4. Люк открыт.** Low angle at the open ceiling hatch, the lid flipped up, red siren light pouring down the ladder into the dark bunker. + ФОН + БУНКЕР
- **Ф5. Вид вверх.** Extreme low angle straight up the ladder through the open round hatch into a dark village garage above: wooden roof beams, a hanging lamp glowing red, open garage door with snow falling outside at night. + ФОН
- **Ф6. Забор, год назад.** Snowy Eastern European village street at warm sunset, a wooden fence between two yards, garages and power lines, soft golden light. + ФОН
- **Ф7. Склад.** Close view of bunker storage shelves full of canned food and wooden crates, a clipboard with a pencil hanging on a nail. + ФОН + БУНКЕР

## Персонажи (каждый отдельной картинкой, на прозрачном фоне)

**Герой:** a man in his 30s with a round head, short dark hair, light stubble, blue padded quilted work jacket with an orange reflective stripe, dark work trousers, tan work boots, black mittens. + ПЕРСОНАЖ
- Г1 standing, looking up, worried face
- Г2 standing, holding a smartphone and looking at the screen, sad face
- Г3 standing, thinking, hand on chin
- Г4 sitting on a bench, thinking face, side view three-quarters
- Г5 climbing a ladder, back three-quarters view, reaching up with one hand, determined face
- Г6 standing, shocked face, mouth open
- Г7 standing, waving with a smile

**Друг:** a man in his 30s in a military camouflage jacket and trousers, camouflage cap, army boots. + ПЕРСОНАЖ
- Д1 climbing down a ladder, back view, looking over his shoulder, serious face
- Д2 standing, saying something quietly, serious face

**Семья (сидят на лавке):** + ПЕРСОНАЖ
- С1 grandfather in an ushanka hat and grey quilted vest over a sweater, sitting, tired face
- С2 mother with long brown hair in a mustard knitted cardigan, sitting, worried face
- С3 boy about 10 in a red puffer jacket and blue beanie, sitting, scared face
- С4 girl about 8 in a red puffer jacket and blue beanie, sitting, scared face

**Соседи:** + ПЕРСОНАЖ
- Н1 woman in a purple winter jacket with a fur hood, leaning forward and looking down, anxious face
- Н2 man in an olive green parka, leaning forward and looking down, stern face
- Н3 man in a brown winter jacket and grey beanie, leaning forward and looking down, desperate face
- Н4 the woman from Н1 standing behind a fence and waving with a smile

## Сборка сцен (что я накладываю)

| # | Текст | Фон | Персонажи и действие |
|---|---|---|---|
| 1 | «...А в люк стучит шестой» | Ф1 | Г1 входит под люк; крышка дрожит (тряска кадра) |
| 2 | «Сирены стихли. Это друг...» | Ф1 | Г2, на телефоне появляются сообщения |
| 3 | «Ты стоишь у люка и считаешь...» | Ф1 | Г3 у лестницы, облако мыслей с чеками |
| 4 | «...на шестерых: двадцать месяцев» | Ф2 | С1, С2, Г4, С3, С4 на лавке, шестое место пустое |
| 5 | «Вода из скважины, воздух идёт...» | Ф3 | Г3 (облегчение), значки по очереди |
| 6 | «Ты открываешь» | Ф1 → Ф4 | Г5 лезет вверх, свет сверху |
| 7 | «Друг заходит один... я всё знал» | Ф4 | Д1 спускается, затем Д2; Г6 смотрит |
| 8 | «За ним в свете сирен стоят люди...» | Ф5 | Н1, Н2, Н3 появляются по одному у края люка |
| 9 | «...махал через забор» | Ф6 | Г7 и Н4 машут |
| 10 | «Трое. Если пустить и их...» | Ф7 | Н1–Н3 полупрозрачные силуэты, цифра 13 месяцев |
| 11 | «Друга ты пустил. А их?» | Ф5 | Н1–Н3 смотрят вниз, кнопки ДА/НЕТ |

Итого: 7 фонов + 17 персонажей = 24 картинки на ролик A. Названия файлов при отправке не важны, я разберу по содержимому.
