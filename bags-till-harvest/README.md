# Bags Till Harvest

A rough, playable prototype. A farm family counts its maize harvest in bags, guesses when the
bags will run out, remembers the year's costs one category at a time, then watches the store
empty month by month and adjusts the plan.

It adapts the harvest-planning exercise from Augenblick, Jack, Kaur, Masiye & Swanson,
*Retrieval Failures and Consumption Smoothing: A Field Experiment on Seasonal Poverty*
(forthcoming, QJE). In the study, Zambian farmers set pins standing for bags of grain into
spending-category boxes, prompted one category at a time by a surveyor. Farmers remembered
42% more expenses, and savings two months later were 15% higher.

> **Status: prototype for playing with.** English only. Not checked against the paper's
> surveyor script: the category order, subcategories and wording are my best guess. Emoji
> stand in for real pictures.

## Files

| File | What it is |
|---|---|
| `index.html` | The playable prototype. One file, no build step, no install. |
| `design-sketch.html` | The earlier design sketch: the same screens next to notes on what the study did, what this version changes, and what to test in the field. |

## Run it

Open `index.html` in any browser, on a phone or a laptop. It needs no server. It fetches
two Google Fonts and falls back to system fonts when offline.

It opens with an **example family** filled in. Tap **✨ New plan** to start empty.

## The seven screens

1. **Harvest.** Tap + to add bags to the store. Optionally set what one bag sells for, so
   costs also show in kwacha.
2. **Guess.** Before any counting: *in which month will the bags run out?*
3. **Eating.** How many bags the family eats each month, in half-bag steps.
4. **Remember.** Walk through five categories (School, Home, Farm, People, Surprises). Tap
   a picture card, choose how many bags and which month. The pin lands on the year board.
   Surprises have no month; they become a **keep-safe** reserve guarded from Khoswe the rat.
5. **Play the year.** The store empties one month at a time. Months without maize turn red
   with a `!`. It ends with *You guessed X / Counted Y*.
6. **Fix.** For each cost: smaller (−), earlier (◀), later (▶). Also change eating and the
   keep-safe reserve. The bars update live.
7. **Plan card.** Bags in store at the start of each month. October, December and February
   are the checkpoint months, green when the store still has maize then.

## Features

### Included
- The seven screens above, playable end to end, with back navigation
- Bags as the only unit; half bags allowed
- Optional bag price, which shows costs in kwacha
- 33 picture cards in 5 categories, with ticks on categories already visited
- Year board with pins, animated play-through, guess-vs-count result
- Live fixing of the plan
- Plan card with checkpoint months
- Read-aloud button (🔊) using the phone's built-in text-to-speech
- Every word the user sees comes from one phrase bank
- Works at phone width and on a laptop; light and dark themes; honours "reduce motion"

### Excluded, on purpose, for now
- **Other languages.** The phrase bank is ready for them; only English is written.
- **Saving.** Reloading the page resets it. Nothing is stored or sent anywhere.
- **Recorded audio.** Read-aloud is the device's own synthetic voice, and it is English only.
- **Research mode.** No fixed study script, no logging, no study arms, and the example
  family is always available. The example family's amounts are made up; in a real study
  they would count as extra information given to the farmer.
- **Facilitator or group-session mode**, privacy screen, erase-after-use.
- **Printing or exporting** the plan card.
- **Real illustrations.** Emoji are placeholders.
- **Local calendars.** Months run May to April for the Zambian maize season. School terms
  and checkpoint months are fixed in the code.
- **Safety limits.** Nothing stops a family planning to eat very little.

## Editing the phrase bank

All user-facing text lives in one object near the top of the `<script>` in `index.html`:

```js
const PHRASES = {
  en: {
    next: "Next ▸",
    harvest_say: "Hello! Let's see if your maize lasts <b>until next harvest</b>. ...",
    eat_year: "Over 12 moons that is <b>{n} bags</b> for eating.",
    months: ["May","Jun", ... ,"Apr"],
    items: { fees: "School fees", uniform: "Uniform", ... }
  }
};
let LANG = "en";
```

### Change English wording
Edit the value and keep the key. For example, change `eat_say` to rephrase the eating
question.

### Add a language
1. Copy the whole `en: { ... }` block and paste it below as a new block, for example `ny:`
   for Nyanja or `bem:` for Bemba.
2. Translate the **values** only. Never rename the keys (`harvest_say`, `fees`, ...).
3. Keep `{placeholders}` exactly as written, for example `{n}`, `{m}`, `{h}`, `{r}`. The
   app fills them with numbers and month names. You can move them within the sentence.
4. `months` must stay a list of **12** names, in harvest order starting with May.
5. `items` must keep all 33 keys. Their order doesn't matter.
6. `<b>…</b>` marks a word in bold. Keep it or drop it.
7. Set `LANG = "ny"` (your new code) and reload.

Anything you leave out falls back to English, so you can translate a little at a time.
Most phrases show up in the bubble at the top of the screen. Check each screen at phone
width, because longer languages can wrap.

Read-aloud uses `u.lang = "en"` inside `speak()`. Change it to your language's code too.
Many phones have no voice for Nyanja or Bemba, so expect recorded audio to be needed.

### Phrase keys by screen

| Screen | Keys |
|---|---|
| All | `next`, `done`, `back`, `bags`, `bag`, `bagsEachMoon`, `empty`, `k` |
| Harvest | `harvest_say`, `harvest_unit`, `harvest_sell`, `harvest_price`, `newPlan`, `example`, `exampleShown` |
| Guess | `guess_say`, `guess_lasts` |
| Eating | `eat_say`, `eat_year` |
| Remember | `cat_*` (5 category names), `say_*` (5 category prompts), `board`, `keepSafe`, `sheet_which`, `sheet_surprise`, `sheet_ok`, `items` |
| Play | `play_say`, `play_done_say`, `play_btn`, `play_again`, `play_tap`, `play_tip`, `tip_left`, `tip_none`, `guessed`, `counted`, `harvestWord`, `good`, `good_spare`, `bad`, `bad_one`, `bad_comfort` |
| Fix | `fix_say`, `fix_ok_say`, `fix_ok`, `fix_short`, `eating`, `keepSafeRow`, `noCosts`, `tooSmall` |
| Plan card | `card_say`, `card_legend`, `card_short`, `startAgain`, `erase` |

## Editing anything else

Below the phrase bank, the script has no user-facing words:

- **Items and categories:** `CATS`. Each item is `[key, emoji]`. Adding an item means adding
  it to `CATS` *and* adding its name under `items` in every language.
- **Month icons:** `MONTH_IC`, 12 entries starting in May.
- **Checkpoint months:** `CHECKS = [5,7,9]`, which counts from May = 0, so Oct, Dec, Feb.
- **Example family:** `example()`.
- **Limits:** in `ACTIONS`, for example a harvest of up to 60 bags and eating of up to 6
  bags a month.

## Next steps

1. Check the categories, the order and the wording against the paper's surveyor script.
2. Write Nyanja or Bemba phrases, and try the app with a few farmers alongside the
   facilitated pin exercise.
3. Then decide what comes next: saving, recorded audio, printing the plan card, a
   facilitator mode, making it work offline and installable, or a research mode.
