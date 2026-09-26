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

Live: https://levine63.github.io/Ideas/bags-till-harvest/ (design sketch: `design-sketch.html` in the same folder).

Or open `index.html` in any browser, on a phone or a laptop. It needs no server. It fetches
two Google Fonts and falls back to system fonts when offline.

It opens **empty**. Tap **👀 Try an example family** to load made-up numbers; a banner marks them as an example.

## The seven screens

1. **Harvest.** Tap + to add bags to the store. Optionally set what one bag sells for, so
   costs also show in kwacha.
2. **Guess.** Before any counting: *in which month will the bags run out?*
3. **Eating.** Who eats from the store (adults, children, children in school), then how many
   bags the family eats each month, in half-bag steps.
4. **Remember.** Walk through five categories (School, Home, Farm, People, Surprises). Tap
   a picture card, choose how many bags and which month. The pin lands on the year board.
   Surprises (clinic, medicine, **funeral**, animal dies, something breaks, something else) have
   no month; they become a **keep-safe** reserve guarded from Khoswe the rat. Funeral lives here,
   not under People, because nobody can plan when one comes.
5. **Play the year.** The store empties one month at a time, shown as stacks of sacks (one sack
   per bag; for big harvests each sack is 2 or 5 bags, with a key). Months without maize turn red
   with a `!`. It ends with *Your guess / The count*. If the bags run short, the guide stays
   calm and offers to fix it together. If they last, it celebrates, then asks whether anything
   was forgotten, with a button back to the cost walk.
6. **Fix.** For each cost: smaller (−), earlier (◀), later (▶). Also change eating and the
   keep-safe reserve. The bars update live.
7. **Plan card.** Bags in store at the start of each month. October, December and February
   are the checkpoint months, green when the store still has maize then.

## Features

### Included
- The seven screens above, playable end to end, with back navigation
- Bags as the only unit; half bags allowed
- Optional bag price, which shows costs in kwacha
- 32 picture cards in 5 categories, with ticks on categories already visited
- Year board with pins, animated play-through, guess-vs-count result
- Live fixing of the plan
- Plan card with checkpoint months
- Read-aloud button (🔊) using the phone's built-in text-to-speech
- Visuals: a drawn granary that fills and drains, a maize-cob guide whose face changes (happy, thinking, worried), a season band under every month row (harvest, cool, hot, rains), sacks grouped in 10s
- Small animations: sacks drop in, Khoswe the rat runs in on the Surprises tab, a burst of maize when the plan lasts, rows flash when you change them. All off when the phone asks for reduced motion.
- Costs that fall in red months are marked red on the Fix screen. Eating is at the bottom, with a gentle note if the family cuts it.
- Plan card: check months keep their ✓ even when red; empty months show 0 and a bowl; "Keep this plan" tells people to take a photo; Erase needs two taps.
- Every word the user sees comes from one phrase bank
- Works at phone width and on a laptop; light and dark themes; honours "reduce motion"

- **Three gentle questions**, each asked once, never blocking (tap "Keep mine" / "None this
  year" / "Skip" or just Next):
  - *Food:* if eating is under 75% of what is typical for the family size, the guide asks whether
    it is enough and offers the typical amount.
  - *School:* if children are in school but no School cost was picked.
  - *Keep-safe:* if nothing is kept safe from Khoswe when leaving Surprises.
- **Big celebration** when the plan lasts until harvest: maize rain, a banner, the guide dances.
  It fires after playing the year, and on the Fix screen when a change clears the last red month.
- **No spoilers:** during Play, months not reached yet stay empty.

### Food benchmark and switches

Near the top of the script:

```js
const CHECK = { food:true, school:true, keepSafe:true };
const FOOD  = { kgPerAdultYear:170, childShare:.5, bagKg:50, askBelow:.75 };
```

- `kgPerAdultYear: 170`. Zambia averages about 130 kg of maize per person per year nationally,
  and 150–185 kg in rural farm households (World Bank, *Maize Trade Policies in Zambia*, 2022;
  Choma district figure of 185 kg). Counting a child as half an adult (`childShare`) gives
  roughly 170 kg per adult: 0.28 of a 50 kg bag a month. A family of 2 adults and 4 children is
  typically about 1.1 bags a month. **Confirm locally before any field use.**
- `askBelow: .75`: the food question appears only when the plan is under 75% of typical.
- The food question tells families what is typical, which is outside information the original
  study did not give. Set `CHECK.food = false` for a pure-recall study arm. The school and
  keep-safe questions only jog memory, which is closer to the study's own prompts.

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
3. Keep `{placeholders}` exactly as written, for example `{b}`, `{m}`, `{h}`, `{r}`. The
   app fills them in. You can move them within the sentence. `{b}` is always an amount of
   bags that is already worded, like "1 bag" or "3½ bags".
4. Word amounts of bags with `bag_one` ("{n} bag", for ½ or 1) and `bag_other`
   ("{n} bags"). If your language has different plural rules, change `nb()` in the script.
5. `months` must stay a list of **12** names, in harvest order starting with May.
6. `items` must keep all 32 keys. Their order doesn't matter.
7. `<b>…</b>` marks a word in bold. Keep it or drop it.
8. Set `LANG = "ny"` (your new code) and reload.

Anything you leave out falls back to English, so you can translate a little at a time.
Most phrases show up in the bubble at the top of the screen. Check each screen at phone
width, because longer languages can wrap.

Read-aloud uses `u.lang = "en"` inside `speak()`. Change it to your language's code too.
Many phones have no voice for Nyanja or Bemba, so expect recorded audio to be needed.

### Phrase keys by screen

| Screen | Keys |
|---|---|
| All | `bag_one`, `bag_other`, `next`, `done`, `back`, `bagsEachMoon`, `empty`, `k`, `months`, `seasons` |
| Harvest | `harvest_say`, `harvest_unit`, `harvest_price`, `price_btn`, `example`, `exampleBanner`, `mine` |
| Guess | `guess_say`, `guess_lasts` |
| Eating | `eat_say`, `eat_year`, `adults`, `kids`, `inSchool`, `nudge_food`, `nudge_food_yes`, `nudge_food_no` |
| Remember | `cat_*` (5 category names), `say_*` (5 category prompts), `board`, `keepSafe`, `sheet_which`, `sheet_pick`, `sheet_surprise`, `sheet_ok`, `sheet_none`, `close`, `items`, `nudge_school`, `nudge_school_yes`, `nudge_school_no`, `nudge_safe`, `nudge_safe_yes`, `nudge_safe_no` |
| Play | `play_say`, `play_done_bad`, `play_done_good`, `recheck_q`, `recheck_btn`, `bagkey`, `good_spare_r`, `party`, `play_btn`, `play_again`, `play_tap`, `play_tip`, `tip_left`, `tip_none`, `guessed`, `counted`, `harvestWord`, `good`, `good_spare`, `bad`, `bad_one`, `bad_comfort` |
| Fix | `fix_say` (uses `{minus}` `{earlier}` `{later}` button pictures), `fix_ok_say`, `fix_ok`, `fix_short`, `earlier`, `later`, `eating`, `keepSafeRow`, `noCosts`, `eat_less`, `tooSmall` |
| Plan card | `card_say`, `card_legend`, `card_short`, `keep`, `keep_toast`, `startAgain`, `erase`, `erase_sure` |

## Editing anything else

Below the phrase bank, the script has no user-facing words:

- **Items and categories:** `CATS`. Each item is `[key, emoji]`. Adding an item means adding
  it to `CATS` *and* adding its name under `items` in every language.
- **Month icons and seasons:** `MONTH_IC` and `SEASON`, 12 entries each starting in May.
- **Guide's mood per screen:** `FACE_FOR`.
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
