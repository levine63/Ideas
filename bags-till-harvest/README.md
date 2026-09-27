# Bags Till Harvest

A phone-sized, single-page prototype designed to help a farm family recall the year's costs after
harvest and see whether its maize will last until the next one. The family counts its bags,
guesses how many will go to things that are not food, walks through those costs one category at
a time, adds food last, and watches a month-by-month projection. It is designed with low-literacy
users in mind but has not yet been tested with farmers. It is not affiliated with or reviewed by
the study's authors. [Play the prototype](https://levine63.github.io/Ideas/bags-till-harvest/) ·
[Design notes beside the app](https://levine63.github.io/Ideas/bags-till-harvest/design-sketch.html).

This is the **second pass**, rebuilt from a Claude Design proposal: one question per screen, the
study's order (a guess, then non-food costs, then food), and a stronger take-home.

**Try it:** Tap **My own phone**, then **Try an example family**. In each cost category tap
**What did the example family remember here?** to uncover its costs, then play the year. The
example numbers are invented; tap **Start mine** to use your own. Do this privately: anyone
looking at the screen can see the harvest and costs. Reloading resets the page.

**Research basis.** Augenblick, Jack, Kaur, Masiye, and Swanson, [*Retrieval Failures and Consumption Smoothing: A Field Experiment on Seasonal Poverty*](https://www.nber.org/papers/w35430) (2026 working paper; listed by an author as forthcoming in *The Quarterly Journal of Economics*). In the field experiment, prompted associative recall of future expenses raised remembered expenses by 36–60%; treated households had 15% more savings six weeks later and entered the hungry season with about one additional month of savings. The [earlier 2023 version](https://www.povertyactionlab.org/sites/default/files/research-paper/WP4597_Retrieval-Failures-and-Consumption-Smoothing-in_Zambia_Jack-et-al_Sept2023.pdf) reported 42% more remembered expenses and measured the 15% savings difference two months later. These are outcomes of the **facilitated intervention**, not evidence that this app works.

> **Prototype, not a validated household budget or nutrition tool.** The prompts and sequence
> have not been checked against the study's surveyor script. The month-by-month model treats
> maize as the only stock: it subtracts the same eating amount each month, dated and spread
> costs, and kept-safe bags. It omits other food, cash income, buying grain, changing prices,
> and shocks. A red month means this simplified maize balance is negative; it does not establish
> that a family will go hungry. Users can cut food or costs to turn the forecast green; the app
> then withholds its celebration and reminders and lists the cuts, but do not read a green result
> as advice to eat less or skip a necessary payment.

## Files

| File | What it is |
|---|---|
| `index.html` | The app. One page, no build step, no install, no server. |
| `design-sketch.html` | The app embedded beside design notes. The notes follow the screen the app shows: what the study did, what this version does, and what to test with farmers. Buttons jump the app to any screen with the example family loaded. |
| `art/` | 38 [OpenMoji](https://openmoji.org) pictures (CC BY-SA 4.0), stored locally so the app works offline. Placeholders for local photos; see `art/README.md`. |
| `qrcode.js` | [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 1.4.4 by Kazuhiko Arase (MIT licence), kept beside the app so QR codes work without internet. |

## Run it

Live: [the app](https://levine63.github.io/Ideas/bags-till-harvest/) ·
[presenter version](https://levine63.github.io/Ideas/bags-till-harvest/?presenter=1) ·
[pure-recall version](https://levine63.github.io/Ideas/bags-till-harvest/?outside=off) ·
[design notes](https://levine63.github.io/Ideas/bags-till-harvest/design-sketch.html).

Or open `index.html` in any browser. It fetches two Google Fonts (Archivo, IBM Plex Mono) and
falls back to system fonts when offline. If a phone shows an old version after an update, reload.

## The eight screens

Each screen asks one question, shown large at the top; the round button reads it aloud.

1. **Phone.** "Whose phone is this?" **My own phone** (plan privately; reminders can go in the
   calendar) or **Borrowed phone** (from the presenter; send the plan to yourself, then erase).
2. **Bags.** How many bags of maize? Start **Just harvested** (the year starts in May) or
   **From today** (bags on hand now, with a month picker). Each bag is drawn as a sack.
3. **Guess.** "How many bags will go to things that are not food? Don't count. Just guess." The
   guess is shown in sacks out of the total. It replaces the first pass's guess of the month the
   bags run out, so the guess and the recall are in the same unit.
4. **Remember.** Six categories, one at a time: School, Home, Farm, Giving, Surprises, Other.
   Tapping a picture card opens a sheet: bags in half steps, then a month (only months from the
   start to April) or **Every month** for costs spread over the year. Home items start as
   "every month". Surprises (clinic, medicine, funeral, animal dies, something breaks) have no
   month: **Khoswe the rat** runs in, and these become **kept-safe** bags set aside before the
   year is played. "Not this year" removes a cost. A running total shows the bags remembered.
5. **Food**, last, as in the study. How many people eat from the store, then bags eaten per month.
   The **food check** asks once if eating looks low (see below).
6. **Play the year.** One column per month: a stack of sacks for the bags in the store at the
   start of that month (one sack per bag, or per 2+ bags for big harvests, with a key). Walk with
   **Next month** or **Play all**. Months not reached yet are striped. A short month turns red
   with a `!`. Small squares mark dated costs. The result:
   - **Lasts:** a celebration, spare bags, and kept-safe bags.
   - **Lasts only after cuts** (food, kept-safe bags or any cost on the first complete list was
     reduced or removed): no celebration; the cuts are listed with **Put them back**.
   - **Runs short:** the month it runs out and how many months have no maize.
   - Always: **First guess** versus **Remembered** bars for non-food bags, and **Change food** /
     **Change costs**.
7. **Say it back.** "At the start of {first check month}, how many bags should you have?" Three
   big numbers; then all check months (every three months from the start, up to April). Each
   value is what the farmer will count: bags at the start of that month plus kept-safe bags.
8. **Take home.**
   - **Mark your bags:** how many bags to label for food, each cost category, and kept safe.
   - **Own phone:** opt-in reminders every three months, only for a plan that lasts without
     cuts, never in the presenter version: an `.ics` calendar file and Google Calendar buttons.
     Only future dates are offered.
   - **Borrowed phone:** type the farmer's number, see the SMS, then **SMS** or **WhatsApp**
     (both from this phone), or scan a **QR code** that opens the plan on the farmer's own phone.
     Then **Erase plan from this phone** (two taps).

## Features

### Included
- The eight screens above, with back navigation, in the study's order.
- Bags as the only unit; half bags allowed. Sack icons everywhere bags are counted.
- 34 picture cards in 6 categories, with ✓ for categories with costs and · for visited ones.
- Costs by month or spread over the year; dated costs set before the start month count in the
  start month.
- **First complete list.** When the family first reaches Play the year, the app saves its costs,
  kept-safe bags and food. Later cuts to any of them mean no celebration and no reminders, and
  are listed with **Put them back**. Moving a cost to another month is not a cut.
- Recall bars: the first guess beside the bags remembered.
- Khoswe the rat on the Surprises category.
- **Send the plan:** SMS text for any phone (plain characters, one message), WhatsApp, and a QR
  code whose link carries the whole plan after `#`, which never reaches the web server.
- **Presenter version** (`?presenter=1`): starts on Borrowed phone, no reminders, and a button
  that shows a QR code and WhatsApp link so farmers can open the app on their own phones.
- Read-aloud with the phone's built-in voice; celebration and animations off when the phone asks
  for reduced motion; light and dark themes; keyboard focus kept after each tap.

### Excluded, on purpose, for now
- **Other languages.** The phrase bank is ready; only English is written.
- **Saving on the phone.** Reloading resets the page. A plan survives as a photo, SMS, WhatsApp
  message, QR-code link, or calendar reminders.
- **Recorded audio.** Read-aloud is the device's synthetic voice, English only.
- **Research logging** and fixed study arms (beyond the `?outside=off` switch).
- **Must-pay costs.** Nothing marks school fees or loans as impossible to cut.
- **A check-in screen** at each check month comparing the real bag count with the plan.
- **Local pictures.** OpenMoji mock-ups stand in for local photos.
- **Safety limits.** Nothing stops a family planning to eat very little; the food check only asks.

## Switches

| Switch | Where | Default | When to change |
|---|---|---|---|
| Presenter version | `?presenter=1` in the link | off | turn **on** for a presenter's or shared phone |
| Calendar reminders | `?reminders=off` (or presenter version), or `FEATURES.reminders` | on | the phone is not the farmer's own |
| Outside information | `?outside=off`, or `FEATURES.outsideInfo` | on | a pure-recall study arm: removes the example family, the empty-category hint and the food check |

### Food check

```js
const FOOD = { kgPerPersonYear:150, bagKg:50, askBelow:.75 };
```

On leaving the Food screen, if bags per month are under 75% of 150 kg of maize per person per
year (0.25 of a 50 kg bag a month per person), the app asks once: *"Is ½ bag a month enough for 4
people? Families of 4 often eat about 1 bag a month."* The family can **Use** that amount or
**Keep mine**. **This is a prototype assumption, not a validated consumption standard or a safe
minimum.** An earlier README cited the World Bank's [*Maize Trade Policies in Zambia: Options for Growth*](https://documents1.worldbank.org/curated/en/099845009122237020/pdf/P1770680cbdc81030a9e4092dc8bf6311f.pdf) (2022) for specific 130–185 kg figures, but those figures were not located in that report; that attribution has been removed. The check adds outside information the study did not give, so `?outside=off` turns it off. Do not deploy the benchmark without local validation.

## Group sessions: own phones and borrowed phones

| Situation | What to use | What happens |
|---|---|---|
| Farmer has a smartphone and signal | Presenter version: **📲 Open this app on another phone** | A QR code to scan, or a WhatsApp link. The farmer plans privately on their own phone. |
| Farmer uses the presenter's phone | [Presenter version](https://levine63.github.io/Ideas/bags-till-harvest/?presenter=1), **Borrowed phone** | No reminders. On Take home: SMS, WhatsApp or QR code, then erase before the next family. |
| Taking a plan home to a smartphone | Take home: QR code or WhatsApp | The link opens the plan's Take home screen on the farmer's phone ("Plan received"), where reminders can be turned on. |
| Farmer has a simple phone | Take home: **SMS** | One text, e.g. (illustrative) *"Bags Till Harvest plan. Count your bags (kept-safe too): 1 Dec 9; 1 Mar 4. If fewer, slow down early."* |

The app cannot tell whose phone it is, so presenters must use the presenter link. SMS and
WhatsApp go from the presenter's SIM or account and stay in its sent messages. The QR code is
drawn without internet; opening it needs signal on the farmer's phone.

## Editing the phrase bank

All visible text lives in `PHRASES.en` near the top of the `<script>` in `index.html`.

### Add a language
1. Copy the whole `en: { ... }` block and paste it below as a new block, for example `ny:` for
   Nyanja or `bem:` for Bemba.
2. Translate the **values** only. Never rename the keys.
3. Keep `{placeholders}` exactly as written (`{b}`, `{m}`, `{n}`, `{p}`, `{s}`, `{c}`, `{url}`,
   `{list}` …). You can move them within the sentence. `{b}` and `{s}` are amounts of bags already
   worded, like "1 bag" or "3½ bags".
4. Word amounts of bags with `bag_one` ("{n} bag", for ½ or 1) and `bag_other` ("{n} bags"). If
   your language has other plural rules, change `nb()`.
5. `months` and `monthsLong` must stay lists of **12** names in harvest order, starting with May.
6. `items` must keep all 34 keys.
7. Keep `sms_text` short and free of emoji so it fits in one SMS.
8. Set `LANG = "ny"` and reload. Anything left out falls back to English.

Read-aloud uses `u.lang = "en"` in `speak()`; change it too. Many phones have no voice for Nyanja
or Bemba, so expect recorded audio to be needed.

### Phrase keys by screen

| Screen | Keys |
|---|---|
| All | `bag_one`, `bag_other`, `next`, `next_cat`, `back_aria`, `read_aloud`, `months`, `monthsLong`, `credit` |
| 1 Phone | `say_phone`, `own`, `own_sub`, `borrowed`, `borrowed_sub`, `share_app`, `share_app_head`, `share_wa`, `share_wa_text` |
| 2 Bags | `say_bags`, `just_harvested`, `just_harvested_sub`, `from_today`, `from_today_sub`, `now_month`, `earlier_month`, `later_month`, `bags_unit`, `one_less`, `one_more`, `example`, `example_banner`, `start_mine` |
| 3 Guess | `say_prior`, `prior_sub`, `prior_unit` |
| 4 Remember | `say_school`, `say_home_cat`, `say_farm`, `say_give`, `say_surprise`, `say_other`, `cat_*` (6 names), `cat_line`, `reveal`, `empty_hint`, `remembered`, `items`; sheet: `ask_bags`, `ask_year`, `ask_keep`, `when`, `every_month`, `keep_note`, `save`, `pick_month`, `not_this_year`, `close`, `half_less`, `half_more` |
| 5 Food | `say_food`, `food_sub`, `food_unit`, `food_total`, `people`, `fewer_people`, `more_people`, `nudge_food`, `nudge_yes`, `nudge_no` |
| 6 Play | `say_play`, `store_now`, `store_end`, `kept_safe`, `unit_one`, `unit_many`, `cost_key`, `cap_start`, `cap_month`, `cap_pay`, `cap_left`, `cap_short`, `next_month`, `play_all`, `good_title`, `good_sub`, `good_sub_keep`, `bad_title`, `bad_sub_one`, `bad_sub`, `cut_title`, `cut_q`, `cut_back`, `cut_eat`, `cut_keep`, `recall_head`, `first_guess`, `remembered_bar`, `change_food`, `change_costs`, `play_again`, `party` |
| 7 Say it back | `say_teach`, `teach_sub`, `teach_right`, `teach_wrong`, `teach_days`, `day` |
| 8 Take home | `say_home`, `received`, `mark`, `mark_note`, `lab_food`, `lab_keep`, `remind_head`, `remind_off`, `remind_on`, `remind_ics`, `remind_gcal`, `remind_note`, `remind_wait`, `remind_title`, `remind_details`, `send_head`, `tel_ph`, `sms_text`, `sms_item`, `sms`, `whatsapp`, `send_note`, `qr_btn`, `qr_head`, `no_qr`, `erase`, `erase_sure` |

## Editing anything else

Below the phrase bank, the script has no user-facing words:

- **Items and categories:** `CATS`. Each item is `[key, OpenMoji code, default month]`, where
  months count from May = 0, `ALL` = every month, and `null` = the farmer chooses. Adding an item
  means adding it to `CATS`, a picture to `art/`, and its name under `items` in every language.
- **Example family:** `EX` (its costs) and the `example` action (bags, guess, food, people).
- **Model:** `st()`, `spendIn()`, `run()`, `checks()`, `cuts()`, `works()`.
- **Switches and benchmark:** `PRESENTER`, `FEATURES`, `FOOD`, `STEP_MS` (Play all speed).
- **Plan links:** `planToLink()` and `planFromHash()`: compact JSON, base64-encoded after
  `#plan=`, including the first complete list so cuts still count on the receiving phone. Every
  value read from a link is checked and clamped; unknown items are dropped.
- **Design notes bridge:** the app posts `{bthStep}` to a parent page and accepts `{bthGo}` jumps
  only from the page that frames it.

## Priorities before field use

1. **Check the flow against the surveyor script**: categories, items, order, and whether the
   guess-versus-recall comparison and the food check change the treatment.
2. **Replace the pictures** with local photos or drawings, and test that farmers name each one.
3. **Replace or remove the food benchmark** with a locally checked figure.
4. **Test comprehension privately** on low-end Android phones, offline, with people who read
   little: the guess, kept-safe bags, a red month, the check months, and the labels.
5. **Decide on must-pay costs, on-phone saving, and a check-in screen** for the reminder dates.
6. **Harden the app:** move the model into tested pure functions; add recorded audio.

## Sources

- Augenblick, Ned, B. Kelsey Jack, Supreet Kaur, Felix Masiye, and Nicholas Swanson. 2026. [“Retrieval Failures and Consumption Smoothing: A Field Experiment on Seasonal Poverty.”](https://www.nber.org/papers/w35430) NBER Working Paper 35430. [Author's research page](https://www.supreetkaur.com/research).
- Augenblick et al. 2023. [Earlier working-paper version](https://www.povertyactionlab.org/sites/default/files/research-paper/WP4597_Retrieval-Failures-and-Consumption-Smoothing-in_Zambia_Jack-et-al_Sept2023.pdf).
- World Bank. 2022. [*Maize Trade Policies in Zambia: Options for Growth*](https://documents1.worldbank.org/curated/en/099845009122237020/pdf/P1770680cbdc81030a9e4092dc8bf6311f.pdf). Listed to make the former benchmark attribution auditable; it is **not** cited as support for the app's food constants.
- [OpenMoji](https://openmoji.org) 15.1.0, CC BY-SA 4.0: all pictures in `art/`.
- Arase, Kazuhiko. [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator), version 1.4.4, MIT licence.
