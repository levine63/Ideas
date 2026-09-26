# Bags Till Harvest

A phone-sized, single-page prototype that helps a farm family recall the year's costs after
harvest and see whether its maize will last until the next one. The family counts its bags,
guesses when they will run out, walks through future costs by category, and watches a simple
month-by-month projection. [Play the prototype](https://levine63.github.io/Ideas/bags-till-harvest/) ·
[Design notes beside the app](https://levine63.github.io/Ideas/bags-till-harvest/design-sketch.html).

**Try it:** Tap **👀 Try an example family**, make a guess, and in each cost category tap
**👀 What did the example family remember here?** to uncover its costs. Then play the year.
The example numbers are invented. To use your own numbers, tap **Start mine**. Do this
privately: anyone looking at the screen can see the harvest and costs. Reloading resets the page.

**Research basis.** Augenblick, Jack, Kaur, Masiye, and Swanson, [*Retrieval Failures and Consumption Smoothing: A Field Experiment on Seasonal Poverty*](https://www.nber.org/papers/w35430) (2026 working paper; listed by an author as forthcoming in *The Quarterly Journal of Economics*). In the field experiment, prompted associative recall of future expenses raised remembered expenses by 36–60%; treated households had 15% more savings six weeks later and entered the hungry season with an additional month of savings. The [earlier 2023 version](https://www.povertyactionlab.org/sites/default/files/research-paper/WP4597_Retrieval-Failures-and-Consumption-Smoothing-in_Zambia_Jack-et-al_Sept2023.pdf) reported 42% more remembered expenses and measured the 15% savings difference two months later. These are outcomes of the **facilitated intervention**, not evidence that this app works.

> **Prototype, not a validated household budget or nutrition tool.** The prompts and sequence
> have not been checked against the study's surveyor script. The month-by-month model treats
> maize as the only stock: it subtracts the same eating amount each month, dated and spread
> costs, and a keep-safe reserve. It omits other food, cash income, buying grain, changing
> prices, and shocks. A red month means this simplified maize balance is negative; it does not
> establish that a family will go hungry. Users can still cut eating or costs to turn the
> forecast green. The app withholds its celebration and lists the cuts when that happens, but
> do not read a green result as advice to eat less or skip a necessary payment.

## Files

| File | What it is |
|---|---|
| `index.html` | The app. One page, no build step, no install, no server. |
| `design-sketch.html` | The app embedded beside design notes. The notes follow the screen the app shows: what the study did, what this version does, and what to test with farmers. Buttons jump the app to any screen with the example family loaded. |
| `qrcode.js` | [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 1.4.4 by Kazuhiko Arase (MIT licence), kept beside the app so QR codes work without internet. |

## Run it

Live: [the app](https://levine63.github.io/Ideas/bags-till-harvest/) ·
[presenter version](https://levine63.github.io/Ideas/bags-till-harvest/?presenter=1) ·
[design notes](https://levine63.github.io/Ideas/bags-till-harvest/design-sketch.html).

Or open `index.html` in any browser, on a phone or a laptop. It fetches two Google Fonts and
falls back to system fonts when offline. If a phone shows an old version after an update,
reload the page.

## The seven screens

1. **Harvest.** Tap + to fill a drawn granary with bags; ten sacks group into one. Optionally
   set what one bag sells for, so costs also show in kwacha.
2. **Guess.** Before any counting: *in which month will the bags run out?* A season band
   (harvest, cool, hot, rains) sits under the months.
3. **Eating.** How many people eat from the store (one number), then how many bags they eat
   each month, in half-bag steps.
4. **Remember.** Walk through five categories (School, Home, Farm, People, Surprises). Tap a
   picture card, choose how many bags, and choose a month or **🔁 Spread over the year** for
   costs with no set month. A spread cost is entered as the amount for the whole year, and 1/12
   of it comes out of the store each month. Home items start as spread. To remove a cost, take
   it down to 0 (**Not needed this year**). Surprises (clinic, medicine, funeral, animal dies,
   something breaks, something else) have no month; they become **keep-safe** bags guarded from
   Khoswe the rat. Funeral lives here, not under People, because nobody can plan when one comes.
5. **Play the year.** The store empties one month at a time as stacks of sacks (one sack per
   bag; for big harvests each sack is 2 or 5 bags, with a key). Months not reached yet stay
   blank. A month with no maize left turns red with a `!`. The result says how many costs were
   remembered, then shows *Your guess / The count*. A shortfall gets calm words and a way to
   fix it. A plan that lasts gets a big celebration, then *"Plans that last on the first try
   often miss something"* with a button back to the costs.
6. **Fix.** For each cost: smaller (−), earlier (◀), later (▶). Also change eating and the
   keep-safe bags. The stacks update live, and costs that land in red months are marked red.
7. **Plan card.** Bags in the store at the start of each month; August, November and February
   (every three months) are check months, marked whether or not the stock lasts. From here the
   family can **send the plan to a phone** and, on its own phone, **opt into reminders**
   (see below).

## Features

### Included
- The seven screens above, playable end to end, with back navigation.
- Bags as the only unit; half bags allowed. Optional bag price.
- 32 picture cards in 5 categories, with ticks on categories visited.
- Costs by month, or spread over the year.
- **Three gentle questions**, each asked once and never blocking (answer, or just tap Next):
  - *Food:* if eating is under 75% of a coded, unvalidated benchmark for the number of people,
    the guide asks whether it is enough and offers that amount. This is not a nutritional
    recommendation.
  - *School:* if no School cost was picked ("No children in school" is one answer).
  - *Keep-safe:* if nothing is kept safe from Khoswe when leaving Surprises.
- **Cuts are checked against the first list.** When the family first leaves the cost walk, the
  app saves that cost list and keep-safe amount. If the plan only lasts after cutting eating,
  keep-safe, or any first-list cost, there is no celebration: the app lists what was cut, asks
  whether the family can really do without it, and offers **↩ Put them back**. Moving a cost
  earlier or later is not a cut.
- A month with no maize left is a "moon with no maize", not a hungry moon: the model tracks
  only maize.
- **Calendar reminders**, only for a plan that lasts without cuts, and only after the farmer
  taps **📅 Reminders on my own phone?** One Google Calendar button per check month, or one
  `.ics` file with all of them. Each says how many bags the plan expects in the store, keep-safe
  included. Only future dates are offered. Never shown on presenter phones.
- **Send this plan to a phone** (plan card): a QR code and a WhatsApp link that carry the plan
  inside the link, plus a one-message **SMS** for simple phones (see below).
- **Presenter version** (`?presenter=1`): no reminders, and a button that shows a QR code and
  WhatsApp link so farmers can open the app on their own phones.
- Read-aloud button (🔊) using the phone's built-in voice.
- A drawn granary that fills and drains; a maize-cob guide whose face changes; a season band
  under every month row; sacks grouped in tens.
- Small animations: sacks drop in, Khoswe runs across the Surprises screen, maize rain and a
  banner when a plan lasts, rows flash when changed. All off when the phone asks for reduced
  motion.
- Plan card: check months keep their ✓ even when red; empty months show 0 and a bowl; Erase
  needs two taps.
- Specific screen-reader labels on the Fix screen ("Make School fees smaller by half a bag").
- Works at phone width and on a laptop; light and dark themes.

### Excluded, on purpose, for now
- **Other languages.** The phrase bank is ready for them; only English is written.
- **Saving on the phone.** Reloading resets the page. A plan survives only by sending it to a
  phone (the link carries it) or in calendar reminders.
- **Recorded audio.** Read-aloud is the device's own synthetic voice, English only.
- **Research mode.** No fixed study script, no logging, no study arms. The example family's
  amounts are invented; in a study they would count as extra information given to the farmer.
- **Must-pay costs.** Nothing marks school fees or loans as impossible to cut.
- **Printing** the plan card.
- **Real illustrations.** Emoji are placeholders.
- **Local calendars.** Months run May to April for the Zambian maize season. School terms and
  check months are fixed in the code.
- **Safety limits.** Nothing stops a family planning to eat very little, and green indicates
  only the simplified maize balance.

## Group sessions: own phones and presenter phones

A session can mix farmers who use their own smartphones with farmers who use a presenter's
or officer's phone.

| Situation | What to use | What happens |
|---|---|---|
| Farmer has a smartphone and signal | The presenter opens the [presenter version](https://levine63.github.io/Ideas/bags-till-harvest/?presenter=1) and taps **📲 Open this app on another phone** | A QR code (scan with the phone camera) and a **WhatsApp** share button with the app link. The farmer plans privately on their own phone, with reminders available. |
| Farmer uses a presenter's phone | [Presenter version](https://levine63.github.io/Ideas/bags-till-harvest/?presenter=1) | No reminders, so no family's numbers land in the presenter's calendar. Erase (two taps) or reload before the next family. |
| Taking a plan home to a smartphone | Plan card: **📲 Send this plan to a phone** | A QR code, or a WhatsApp link, that carries the whole plan inside the link (after `#`, which never reaches the web server). Opening it on the farmer's phone shows the plan card with "Plan received"; there the farmer can opt into reminders. Needs signal on the farmer's phone. |
| Farmer has a simple phone | Plan card: **✉️ Send by SMS** | One plain-text SMS with the three check months, for example: *"Bags Till Harvest plan. Count your maize bags: 1 Aug 27 bags; 1 Nov 23 1/2; 1 Feb 19 1/2. If fewer, slow down early."* A simple phone can't scan a QR code or open the app. |

Privacy: WhatsApp and SMS go from the presenter's account or SIM, and the plan stays in its sent
messages; the app says so and suggests deleting the chat. Scanning the QR code sends nothing
through the presenter's accounts. The QR code works offline because `qrcode.js` ships with the
page.

### Switches

| Switch | Where | Default | Turn off when |
|---|---|---|---|
| Presenter version | `?presenter=1` in the link | off | turn **on** for a presenter's or shared phone |
| Calendar reminders | `?reminders=off` in the link (or presenter version), or `FEATURES.reminders` | on | the phone is not the farmer's own |
| Food question | `CHECK.food` | on | a pure-recall study arm, or no locally checked food figure |
| School question | `CHECK.school` | on | a pure-recall study arm needs it off |
| Keep-safe question | `CHECK.keepSafe` | on | a pure-recall study arm needs it off |

### Food benchmark

```js
const CHECK = { food:true, school:true, keepSafe:true };
const FOOD  = { kgPerPersonYear:150, bagKg:50, askBelow:.75 };
```

The code assumes 150 kg of maize per person per year (one household-average figure covering adults and children), 50 kg per bag, and asks when entered monthly eating is below 75% of its calculated amount. For six people, that amount is 1½ bags per month. **These are prototype assumptions, not a validated consumption standard or a safe minimum.** An earlier README cited the World Bank's [*Maize Trade Policies in Zambia: Options for Growth*](https://documents1.worldbank.org/curated/en/099845009122237020/pdf/P1770680cbdc81030a9e4092dc8bf6311f.pdf) (2022) for specific 130–185 kg figures, but those figures were not located in that report; that attribution has been removed.

The food prompt adds external information. The study's associative-recall intervention did not do that. For a research comparison intended to isolate recall, set `CHECK.food = false` and review the other prompts and example-family access with the research team. Do not deploy the current benchmark without local validation.

## Editing the phrase bank

Most visible text lives in one object near the top of the `<script>` in `index.html`. Some
accessibility labels ("less", "more") are still hard-coded.

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
Edit the value and keep the key. For example, change `eat_say` to rephrase the eating question.

### Add a language
1. Copy the whole `en: { ... }` block and paste it below as a new block, for example `ny:` for
   Nyanja or `bem:` for Bemba.
2. Translate the **values** only. Never rename the keys (`harvest_say`, `fees`, ...).
3. Keep `{placeholders}` exactly as written, for example `{b}`, `{m}`, `{h}`, `{r}`, `{url}`,
   `{list}`. The app fills them in. You can move them within the sentence. `{b}` is always an
   amount of bags that is already worded, like "1 bag" or "3½ bags".
4. Word amounts of bags with `bag_one` ("{n} bag", for ½ or 1) and `bag_other` ("{n} bags"). If
   your language has different plural rules, change `nb()` in the script.
5. `months` and `monthsLong` must stay lists of **12** names, in harvest order starting with May.
6. `items` must keep all 32 keys. Their order doesn't matter.
7. `<b>…</b>` marks a word in bold. Keep it or drop it.
8. Keep `sms_text` short and free of emoji so it fits in one SMS.
9. Set `LANG = "ny"` (your new code) and reload.

Anything you leave out falls back to English, so you can translate a little at a time. Most
phrases show up in the bubble at the top of the screen. Check each screen at phone width,
because longer languages can wrap.

Read-aloud uses `u.lang = "en"` inside `speak()`. Change it to your language's code too. Many
phones have no voice for Nyanja or Bemba, so expect recorded audio to be needed.

### Phrase keys by screen

| Screen | Keys |
|---|---|
| All | `bag_one`, `bag_other`, `next`, `done`, `back`, `bagsEachMoon`, `empty`, `k`, `months`, `monthsLong`, `seasons` |
| Harvest | `harvest_say`, `harvest_unit`, `harvest_price`, `price_btn`, `example`, `exampleBanner`, `mine`, `share_app`, `share_app_head`, `share_wa_text` |
| Guess | `guess_say`, `guess_lasts` |
| Eating | `eat_say`, `eat_year`, `people`, `nudge_food`, `nudge_food_yes`, `nudge_food_no` |
| Remember | `cat_*` (5 category names), `say_*` (5 category prompts), `board`, `keepSafe`, `sheet_which`, `sheet_pick`, `sheet_surprise`, `ex_reveal`, `sheet_ok`, `sheet_none`, `spread`, `spread_short`, `sheet_year`, `close`, `items`, `nudge_school`, `nudge_school_yes`, `nudge_school_no`, `nudge_safe`, `nudge_safe_yes`, `nudge_safe_no` |
| Play | `play_say`, `play_done_bad`, `play_done_good`, `recheck_q`, `recheck_btn`, `remembered`, `remembered_one`, `cut_say`, `bagkey`, `good_spare_r`, `party`, `play_btn`, `play_again`, `play_tap`, `play_tip`, `tip_left`, `tip_none`, `guessed`, `counted`, `harvestWord`, `good`, `good_spare`, `bad`, `bad_one`, `bad_comfort` |
| Fix | `fix_say` (uses `{minus}` `{earlier}` `{later}` button pictures), `fix_ok_say`, `fix_ok`, `fix_short`, `earlier`, `later`, `eating`, `keepSafeRow`, `noCosts`, `eat_less`, `tooSmall`, `sr_less`, `sr_more`, `sr_earlier`, `sr_later` |
| Plan card | `card_say`, `card_legend`, `card_spread`, `card_short`, `keep`, `keep_toast`, `received`, `remind_ask`, `remind_why`, `remind_head`, `remind_btn`, `remind_all`, `remind_note`, `remind_title`, `remind_details`, `send_plan`, `send_head`, `send_wa`, `send_wa_text`, `send_sms`, `sms_text`, `sms_item`, `sms_note`, `send_presenter`, `send_note`, `no_qr`, `cut_head`, `cut_q`, `cut_back`, `cut_tip`, `cut_card`, `cut_eat`, `keepSafeShort`, `startAgain`, `erase`, `erase_sure` |

## Editing anything else

Below the phrase bank, the script has no user-facing words:

- **Items and categories:** `CATS`. Each item is `[key, emoji]`. Adding an item means adding it
  to `CATS` *and* adding its name under `items` in every language.
- **Month icons and seasons:** `MONTH_IC` and `SEASON`, 12 entries each starting in May.
- **Guide's mood per screen:** `FACE_FOR`.
- **Which categories start as "spread over the year":** `SPREAD_BY_DEFAULT = ["home"]`.
- **Check months:** `CHECKS = [3,6,9]`, which counts from May = 0, so Aug, Nov, Feb.
- **Presenter and feature switches:** `PRESENTER`, `FEATURES`, `CHECK`, `FOOD`.
- **Example family:** `example()` (its costs are in `exPicks`).
- **Plan links:** `planToLink()` and `planFromHash()`. The plan is compact JSON, base64-encoded
  after `#plan=`.
- **Limits:** in `ACTIONS`, for example a harvest of up to 60 bags and eating of up to 6 bags a
  month.

## Priorities before field use

1. **Keep the recall result visible.** *Partly done:* the first complete cost list is saved and
   cuts are measured against it; the Play result shows how many costs were remembered and the gap
   to the guess. Still to do: show which categories added the most remembered costs.
2. **Handle an infeasible plan honestly.** *Partly done:* no celebration for a plan that only
   lasts after cuts, and a shortfall is shown as "short by N bags" with a pointer to help. Still
   to do: distinguish an expense that can be moved from a bill that must be paid, and validate
   any food guidance locally.
3. **Test comprehension privately.** Ask farmers what a red month, keep-safe, bag price, the
   check months, and "send this plan" mean. Test on low-end Android phones, offline, with people
   who read little. Compare a private facilitated card activity with solo phone use and assisted
   use; do not display personal amounts in a group.
4. **Make return use plausible.** *Partly done:* opt-in reminders at the check months, and plans
   sent to the farmer's own phone by link or SMS. Still to do: opt-in saving on the phone and a
   check-in screen that compares the real bag count with the plan.
5. **Then harden the app.** Move the model into pure functions with tests for half bags, dated
   and spread costs, zero and overdrawn balances; label all controls by item and action for
   screen readers; set read-aloud language per translation and supply recorded audio if needed.

## Sources

- Augenblick, Ned, B. Kelsey Jack, Supreet Kaur, Felix Masiye, and Nicholas Swanson. 2026. [“Retrieval Failures and Consumption Smoothing: A Field Experiment on Seasonal Poverty.”](https://www.nber.org/papers/w35430) NBER Working Paper 35430. [Author's research page](https://www.supreetkaur.com/research).
- Augenblick et al. 2023. [Earlier working-paper version](https://www.povertyactionlab.org/sites/default/files/research-paper/WP4597_Retrieval-Failures-and-Consumption-Smoothing-in_Zambia_Jack-et-al_Sept2023.pdf).
- World Bank. 2022. [*Maize Trade Policies in Zambia: Options for Growth*](https://documents1.worldbank.org/curated/en/099845009122237020/pdf/P1770680cbdc81030a9e4092dc8bf6311f.pdf). Listed to make the former benchmark attribution auditable; it is **not** cited as support for the app's food constants.
- Arase, Kazuhiko. [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator), version 1.4.4, MIT licence.
