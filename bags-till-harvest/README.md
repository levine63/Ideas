# Bags Till Harvest

A phone-sized, single-file prototype for recalling expenses after harvest. The family enters its maize bags, makes an initial guess, walks through future costs by category, and sees a simple month-by-month projection. [Play the prototype](https://levine63.github.io/Ideas/bags-till-harvest/).

**Try it:** Tap **Try an example family**, make a guess, inspect the picture cards, and play the year. The example numbers are invented. To use personal numbers, tap **Start mine**. Do this privately: anyone looking at the screen can see the entered harvest and expenses. Reloading resets the page; **Keep this plan** only asks you to take a photo.

**Research basis.** Augenblick, Jack, Kaur, Masiye, and Swanson, [*Retrieval Failures and Consumption Smoothing: A Field Experiment on Seasonal Poverty*](https://www.nber.org/papers/w35430) (2026 working paper; listed by an author as forthcoming in *The Quarterly Journal of Economics*). In the field experiment, prompted associative recall of future expenses raised remembered expenses by 36–60%; treated households had 15% more savings six weeks later and entered the hungry season with an additional month of savings. The [earlier 2023 version](https://www.povertyactionlab.org/sites/default/files/research-paper/WP4597_Retrieval-Failures-and-Consumption-Smoothing-in_Zambia_Jack-et-al_Sept2023.pdf) reported 42% more remembered expenses and measured the 15% savings difference two months later. These are outcomes of the **facilitated intervention**, not evidence that this app works.

> **Prototype, not a validated household budget or nutrition tool.** The prompts and sequence have not been checked against the study's surveyor script. The month-by-month model treats maize as the only stock: it subtracts the same eating amount each month, dated expenses, and a reserve. It omits other food, cash income, buying grain, changing prices, and shocks. A red month means this simplified maize balance is negative; it does not establish that a family will go hungry. The app currently lets users reduce eating or expenses to turn the forecast green. Do not interpret that as advice to eat less or skip a necessary payment.

## Files

| File | What it is |
|---|---|
| `index.html` | The playable prototype. One file, no build step, no install. |
| `design-sketch.html` | The earlier design sketch: the same screens next to notes on what the study did, what this version changes, and what to test in the field. |

## Run it

Live: [Bags Till Harvest](https://levine63.github.io/Ideas/bags-till-harvest/) · [Design sketch](https://levine63.github.io/Ideas/bags-till-harvest/design-sketch.html).

Or open `index.html` in any browser, on a phone or a laptop. It needs no server. It fetches
two Google Fonts and falls back to system fonts when offline.

It opens **empty**. Tap **👀 Try an example family** to load made-up numbers; a banner marks them as an example.

## The seven screens

1. **Harvest.** Tap + to add bags to the store. Optionally set what one bag sells for, so
   costs also show in kwacha.
2. **Guess.** Before any counting: *in which month will the bags run out?*
3. **Eating.** Who eats from the store (adults and children; children in school is a subset), then how many
   bags the family eats each month, in half-bag steps.
4. **Remember.** Walk through five categories (School, Home, Farm, People, Surprises). Tap
   a picture card, choose how many bags and which month. The pin lands on the year board.
   Surprises (clinic, medicine, **funeral**, animal dies, something breaks, something else) have
   no month; they become a **keep-safe** reserve guarded from Khoswe the rat. Funeral lives here,
   not under People, because nobody can plan when one comes.
5. **Play the year.** The store empties one month at a time, shown as stacks of sacks (one sack
   per bag; for big harvests each sack is 2 or 5 bags, with a key). Months with a negative projected balance turn red
   with a `!`. It ends with *Your guess / The count*. If the projected balance runs short, the guide stays
   calm and offers a revision screen. If they last, it celebrates, then asks whether anything
   was forgotten, with a button back to the cost walk.
6. **Revise.** For each cost: smaller (−), earlier (◀), later (▶). Also change eating and the
   keep-safe reserve. The bars update live. These controls can make an unrealistic plan look successful; see [Priorities before field use](#priorities-before-field-use).
7. **Plan card.** Bags in store at the start of each month. October, December and February
   are the checkpoint months, marked as checkpoints, whether or not the projected stock lasts.

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
- Most visible phrases come from one phrase bank; some labels and accessibility text are hard-coded
- Works at phone width and on a laptop; light and dark themes; honours "reduce motion"

- **Three gentle questions**, each asked once, never blocking (tap "Keep mine" / "None this
  year" / "Skip" or just Next):
  - *Food:* if eating is under 75% of a coded, unvalidated benchmark for family size, the guide asks whether
    it is enough and offers that amount. This is not a nutritional recommendation.
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

The code assumes 170 kg of maize per adult equivalent per year, children at half an adult equivalent, 50 kg per bag, and asks when entered monthly eating is below 75% of its calculated amount. For two adults and four children, that amount is about 1.13 bags per month, rounded up to 1½ in the prompt. **These are prototype assumptions, not a validated consumption standard or a safe minimum.** The previous README cited the World Bank's [*Maize Trade Policies in Zambia: Options for Growth*](https://documents1.worldbank.org/curated/en/099845009122237020/pdf/P1770680cbdc81030a9e4092dc8bf6311f.pdf) (2022) for specific 130–185 kg figures, but those figures were not located in that report; that attribution has been removed.

The food prompt adds external information. The study's associative-recall intervention did not do that. For a research comparison intended to isolate recall, set `CHECK.food = false` and review the other prompts and example-family access with the research team. Do not deploy the current benchmark without local validation.

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
- **Safety limits.** Nothing stops a family planning to eat very little, and green indicates only the simplified maize balance.

## Editing the phrase bank

Most visible text lives in one object near the top of the `<script>` in `index.html`. Some strings in markup and accessibility labels still need to be moved there:

```js
const PHRASES = {
  en: {
    next: "Next ▸",
    harvest_say: "Hello! Let's see if your maize lasts <b>until next harvest</b>. ...",
    eat_year: "For the whole year that is <b>{b}</b>.",
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

## Priorities before field use

1. **Keep the recall result visible.** Record the first guess and first complete cost list before any revisions. Show newly remembered categories and the gap to the initial guess. Let the participant inspect costs without pressure to make the projection green.
2. **Handle an infeasible plan honestly.** Distinguish an expense that can be moved from a bill that must be paid; show unfunded needs if the harvest is too small. Do not celebrate a green result obtained by cutting food or deleting essential costs. Validate any food guidance locally.
3. **Test comprehension privately.** Ask farmers what a red month, reserve, bag price, and “keep plan” mean. Test on low-end Android phones, offline, with people who read little. Compare a private facilitated card activity with solo phone use and assisted use; do not display personal amounts in a group.
4. **Make return use plausible.** Try a private take-home card or opt-in on-device plan that can be revisited at a school-fee or input-purchase date. The current page forgets everything on reload.
5. **Then harden the app.** Move the model into pure functions with tests for half bags, dated costs, zero and overdrawn balances; separate first-pass entries from revisions; label controls by item and action for screen readers; set read-aloud language per translation and supply recorded audio if needed.

## Sources

- Augenblick, Ned, B. Kelsey Jack, Supreet Kaur, Felix Masiye, and Nicholas Swanson. 2026. [“Retrieval Failures and Consumption Smoothing: A Field Experiment on Seasonal Poverty.”](https://www.nber.org/papers/w35430) NBER Working Paper 35430. [Author's research page](https://www.supreetkaur.com/research).
- Augenblick et al. 2023. [Earlier working-paper version](https://www.povertyactionlab.org/sites/default/files/research-paper/WP4597_Retrieval-Failures-and-Consumption-Smoothing-in_Zambia_Jack-et-al_Sept2023.pdf).
- World Bank. 2022. [*Maize Trade Policies in Zambia: Options for Growth*](https://documents1.worldbank.org/curated/en/099845009122237020/pdf/P1770680cbdc81030a9e4092dc8bf6311f.pdf). Listed to make the former benchmark attribution auditable; it is **not** cited as support for the app's food constants.

