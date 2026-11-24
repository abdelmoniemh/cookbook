// Synthetic demo data for the dev mock API. Every title, ingredient and step here is made up.
// Never put content from a real cookbook in this file.

export const SOURCES = [
  { id: 1, name: 'Demo Prep Book' },
  { id: 2, name: 'Demo Quick Meals' },
]

// Food-ish colours for the placeholder "photos" (plate, background, three topping blobs).
const PALETTES = [
  ['#6b3a22', '#d9b38c', '#f2e2c4', '#8aa14b', '#c2492f'],
  ['#2d3b2a', '#c9a15e', '#f4d27a', '#e46a3a', '#7aa35a'],
  ['#3b2f2a', '#b5543a', '#e8c39e', '#f0e6d2', '#5c8a3c'],
  ['#20313f', '#e0b04a', '#f7e3a1', '#d8573a', '#89b35b'],
  ['#3a2a3f', '#c46b4f', '#f1c9a5', '#ffe9c2', '#6f9e48'],
  ['#2f2a24', '#8c5a3c', '#d9a066', '#f3dfb8', '#b23a2a'],
]

const A = {
  produce: 'Produce',
  meat: 'Meat & Fish',
  dairy: 'Dairy & Eggs',
  grains: 'Pasta, Rice & Grains',
  pantry: 'Sauces & Pantry',
  spice: 'Spices & Seasonings',
  other: 'Other',
  skip: 'Skip',
}

// [qty, unit, item, prep, canonical, aisle]  (qty null = as needed)
const I = (qty, unit, item, aisle, opts = {}) => ({ qty, unit, item, aisle, ...opts })

const RAW = [
  {
    title: 'Smoky Paprika Chicken & Rice Boxes', source: 1, page: 12, servings: 4,
    kcal: 512, protein: 48, carbs: 55, fat: 10, tags: ['main', 'chicken', 'meal prep', 'rice'],
    blurb: 'Oven-baked chicken thighs with a smoky dry rub, fluffy rice and charred peppers. Holds up all week in the fridge.',
    groups: [
      { name: 'Chicken', items: [
        I(800, 'g', 'Boneless Chicken Thighs', A.meat, { prep: 'trimmed', canonical: 'chicken thigh' }),
        I(2, 'tsp', 'Smoked Paprika', A.spice, { canonical: 'smoked paprika' }),
        I(1, 'tsp', 'Garlic Powder', A.spice, { canonical: 'garlic powder' }),
        I(10, 'ml', 'Olive Oil', A.pantry, { canonical: 'olive oil' }),
        { kind: 'note', raw: 'Pat the chicken dry before seasoning.' },
      ] },
      { name: 'Rice & Veg', items: [
        I(300, 'g', 'Basmati Rice', A.grains, { prep: 'uncooked', canonical: 'basmati rice' }),
        I(3, null, 'Bell Peppers', A.produce, { prep: 'sliced', canonical: 'bell pepper' }),
        I(1, null, 'Red Onion', A.produce, { prep: 'wedged', canonical: 'red onion' }),
        I(null, null, 'Salt & Pepper', A.spice, { canonical: 'salt' }),
      ] },
    ],
    steps: [
      'Heat the oven to 220°C (200°C fan). Line a large tray with baking paper.',
      'Toss the chicken with the oil, paprika, garlic powder and a good pinch of salt.',
      'Spread the chicken, peppers and onion over the tray and roast for 25 minutes, turning once.',
      'Meanwhile cook the rice according to the packet, then fluff with a fork.',
      'Slice the chicken, divide rice, chicken and veg between four containers and cool before chilling.',
    ],
    notes: ['Keeps 4 days in the fridge.', 'Reheat until piping hot, splash of water over the rice first.'],
    videos: { youtube: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
  },
  {
    title: 'Beef & Black Bean Burrito Bowls', source: 1, page: 18, servings: 4,
    kcal: 585, protein: 46, carbs: 62, fat: 16, tags: ['main', 'beef', 'meal prep', 'rice', 'bowl'],
    blurb: 'Lean mince cooked down with cumin and lime, over rice with beans, corn and a quick yoghurt sauce.',
    groups: [
      { name: 'Beef', items: [
        I(700, 'g', 'Lean Beef Mince (5% fat)', A.meat, { canonical: 'beef mince' }),
        I(1, 'tsp', 'Ground Cumin', A.spice, { canonical: 'cumin' }),
        I(1, 'tsp', 'Chilli Flakes', A.spice, { canonical: 'chilli flakes' }),
        I(1, null, 'Lime', A.produce, { prep: 'juiced', canonical: 'lime' }),
      ] },
      { name: 'Bowl', items: [
        I(280, 'g', 'Long Grain Rice', A.grains, { canonical: 'long grain rice' }),
        I(1, 'can', 'Black Beans', A.pantry, { prep: 'drained', canonical: 'black beans' }),
        I(150, 'g', 'Sweetcorn', A.pantry, { canonical: 'sweetcorn' }),
        I(200, 'g', 'Fat-Free Greek Yoghurt', A.dairy, { canonical: 'greek yoghurt' }),
        { kind: 'note', raw: 'Use any rice you have; adjust the cooking time.' },
      ] },
    ],
    steps: [
      'Brown the mince in a hot non-stick pan, breaking it up, for 6 to 8 minutes.',
      'Add cumin, chilli and a splash of water; simmer 5 minutes, then squeeze in the lime.',
      'Cook the rice. Warm the beans and corn together.',
      'Stir a pinch of salt into the yoghurt for the sauce.',
      'Build the bowls: rice, beef, beans and corn, yoghurt on the side.',
    ],
    notes: ['Freeze the beef portion separately for up to 2 months.'],
    videos: { tiktok: 'https://www.tiktok.com/@demo/video/1', instagram: 'https://www.instagram.com/p/demo1/' },
  },
  {
    title: 'Overnight Protein Oats', source: 2, page: 6, servings: 2,
    kcal: 395, protein: 32, carbs: 48, fat: 8, tags: ['breakfast', 'meal prep'],
    blurb: 'Five minutes the night before, breakfast sorted. Thick, creamy and not too sweet.',
    groups: [
      { name: null, items: [
        I(100, 'g', 'Rolled Oats', A.grains, { canonical: 'rolled oats' }),
        I(1, 'scoop', 'Vanilla Protein Powder', A.other, { canonical: 'protein powder' }),
        I(250, 'ml', 'Skimmed Milk', A.dairy, { canonical: 'milk' }),
        I(100, 'g', 'Fat-Free Greek Yoghurt', A.dairy, { canonical: 'greek yoghurt' }),
        I(80, 'g', 'Frozen Berries', A.produce, { canonical: 'frozen berries' }),
      ] },
    ],
    steps: [
      'Whisk the protein powder into the milk until there are no lumps.',
      'Stir in the oats and yoghurt, then divide between two jars.',
      'Top with berries, seal and chill overnight.',
    ],
    notes: ['Add a splash more milk in the morning if it is too thick.'],
    videos: {},
  },
  {
    title: 'Garlic Butter Salmon with Greens', source: 2, page: 22, servings: 2,
    kcal: 468, protein: 39, carbs: 14, fat: 28, tags: ['main', 'seafood'],
    blurb: 'Pan-seared salmon with a light garlic butter, wilted spinach and green beans.',
    groups: [
      { name: null, items: [
        I(2, null, 'Salmon Fillets', A.meat, { canonical: 'salmon fillet' }),
        I(10, 'g', 'Light Butter', A.dairy, { canonical: 'butter' }),
        I(3, 'clove', 'Garlic', A.produce, { prep: 'minced', canonical: 'garlic' }),
        I(200, 'g', 'Green Beans', A.produce, { prep: 'trimmed', canonical: 'green beans' }),
        I(100, 'g', 'Baby Spinach', A.produce, { canonical: 'spinach' }),
        I(1, null, 'Lemon', A.produce, { canonical: 'lemon' }),
      ] },
    ],
    steps: [
      'Season the salmon and sear skin-side down for 4 minutes until crisp.',
      'Flip, add the butter and garlic, and baste for 2 minutes.',
      'Steam the beans for 4 minutes; wilt the spinach in the same pan.',
      'Serve with lemon wedges.',
    ],
    notes: [],
    videos: { youtube: 'https://www.youtube.com/watch?v=demo2' },
  },
  {
    title: 'Teriyaki Chicken Noodle Prep', source: 1, page: 31, servings: 5,
    kcal: 498, protein: 44, carbs: 58, fat: 9, tags: ['main', 'chicken', 'meal prep', 'noodles'],
    blurb: 'Sticky homemade teriyaki with egg noodles, broccoli and sesame.',
    groups: [
      { name: 'Sauce', items: [
        I(60, 'ml', 'Light Soy Sauce', A.pantry, { canonical: 'soy sauce' }),
        I(2, 'tbsp', 'Honey', A.pantry, { canonical: 'honey' }),
        I(1, 'tbsp', 'Rice Vinegar', A.pantry, { canonical: 'rice vinegar' }),
        I(1, 'tsp', 'Cornflour', A.pantry, { canonical: 'cornflour' }),
        I(null, null, 'Water', A.skip, { canonical: 'water' }),
      ] },
      { name: 'Noodles', items: [
        I(900, 'g', 'Chicken Breast', A.meat, { prep: 'cubed', canonical: 'chicken breast' }),
        I(250, 'g', 'Egg Noodles', A.grains, { canonical: 'egg noodles' }),
        I(1, null, 'Broccoli Head', A.produce, { prep: 'in florets', canonical: 'broccoli' }),
        I(1, 'tsp', 'Sesame Seeds', A.spice, { canonical: 'sesame seeds' }),
      ] },
    ],
    steps: [
      'Whisk the sauce ingredients with 60 ml water.',
      'Stir-fry the chicken in batches until golden, about 6 minutes.',
      'Add the broccoli and a splash of water, cover for 3 minutes.',
      'Pour in the sauce and bubble until glossy.',
      'Toss through the cooked noodles and finish with sesame.',
    ],
    notes: ['Undercook the noodles by a minute; they soften on reheating.'],
    videos: { instagram: 'https://www.instagram.com/p/demo3/' },
  },
  {
    title: 'Turkey Meatball Marinara Pasta', source: 1, page: 40, servings: 4,
    kcal: 560, protein: 47, carbs: 64, fat: 11, tags: ['main', 'meal prep', 'pasta'],
    blurb: 'Baked turkey meatballs in a quick tomato sauce, with high-protein pasta.',
    groups: [
      { name: 'Meatballs', items: [
        I(600, 'g', 'Turkey Mince', A.meat, { canonical: 'turkey mince' }),
        I(1, null, 'Egg', A.dairy, { canonical: 'egg' }),
        I(30, 'g', 'Breadcrumbs', A.pantry, { canonical: 'breadcrumbs' }),
        I(1, 'tsp', 'Dried Oregano', A.spice, { canonical: 'oregano' }),
      ] },
      { name: 'Sauce & Pasta', items: [
        I(2, 'can', 'Chopped Tomatoes', A.pantry, { canonical: 'chopped tomatoes' }),
        I(2, 'clove', 'Garlic', A.produce, { prep: 'crushed', canonical: 'garlic' }),
        I(320, 'g', 'Protein Pasta', A.grains, { canonical: 'pasta' }),
        I(40, 'g', 'Parmesan', A.dairy, { prep: 'grated', canonical: 'parmesan' }),
      ] },
    ],
    steps: [
      'Mix the meatball ingredients and roll into 20 balls.',
      'Bake at 200°C for 18 minutes.',
      'Simmer tomatoes and garlic for 10 minutes; season.',
      'Cook the pasta, then combine everything with the sauce.',
      'Divide into containers and top with parmesan.',
    ],
    notes: [],
    videos: {},
  },
  {
    title: 'Chocolate Peanut Protein Bars', source: 2, page: 44, servings: 8,
    kcal: 214, protein: 16, carbs: 20, fat: 8, tags: ['dessert', 'meal prep'],
    blurb: 'No-bake bars for the gym bag. Chewy, chocolatey, done in the fridge.',
    groups: [
      { name: null, items: [
        I(120, 'g', 'Oat Flour', A.grains, { canonical: 'oat flour' }),
        I(2, 'scoop', 'Chocolate Protein Powder', A.other, { canonical: 'protein powder' }),
        I(60, 'g', 'Peanut Butter', A.pantry, { canonical: 'peanut butter' }),
        I(60, 'ml', 'Maple Syrup', A.pantry, { canonical: 'maple syrup' }),
        I(40, 'g', 'Dark Chocolate', A.pantry, { prep: 'melted', canonical: 'dark chocolate' }),
      ] },
    ],
    steps: ['Stir everything except the chocolate into a stiff dough.', 'Press into a lined tin, drizzle with chocolate, chill 2 hours.', 'Slice into 8 bars.'],
    notes: ['Store in the fridge for up to a week.'],
    videos: { tiktok: 'https://www.tiktok.com/@demo/video/2' },
  },
  {
    title: 'Lemon Herb Chicken Potato Traybake', source: 1, page: 52, servings: 4,
    kcal: 476, protein: 45, carbs: 42, fat: 12, tags: ['main', 'chicken', 'meal prep', 'potato'],
    blurb: 'Everything on one tray: chicken breast, baby potatoes and courgette with lemon and thyme.',
    groups: [
      { name: null, items: [
        I(800, 'g', 'Chicken Breast', A.meat, { canonical: 'chicken breast' }),
        I(800, 'g', 'Baby Potatoes', A.produce, { prep: 'halved', canonical: 'potato' }),
        I(2, null, 'Courgettes', A.produce, { prep: 'chunks', canonical: 'courgette' }),
        I(1, null, 'Lemon', A.produce, { canonical: 'lemon' }),
        I(1, 'tsp', 'Dried Thyme', A.spice, { canonical: 'thyme' }),
        I(15, 'ml', 'Olive Oil', A.pantry, { canonical: 'olive oil' }),
      ] },
    ],
    steps: ['Par-boil the potatoes for 8 minutes.', 'Toss all ingredients on a tray and roast at 210°C for 30 minutes.', 'Rest 5 minutes, slice and portion.'],
    notes: [],
    videos: {},
  },
  {
    title: 'Korean-Style Beef Rice Bowls', source: 1, page: 60, servings: 4,
    kcal: 545, protein: 42, carbs: 60, fat: 14, tags: ['main', 'beef', 'meal prep', 'rice', 'bowl'],
    blurb: 'Sweet-savoury beef with quick pickled cucumber and spring onions.',
    groups: [
      { name: null, items: [
        I(650, 'g', 'Lean Beef Mince (5% fat)', A.meat, { canonical: 'beef mince' }),
        I(3, 'tbsp', 'Light Soy Sauce', A.pantry, { canonical: 'soy sauce' }),
        I(1, 'tbsp', 'Chilli Paste', A.pantry, { canonical: 'chilli paste' }),
        I(280, 'g', 'Jasmine Rice', A.grains, { canonical: 'jasmine rice' }),
        I(1, null, 'Cucumber', A.produce, { canonical: 'cucumber' }),
        I(4, null, 'Spring Onions', A.produce, { canonical: 'spring onion' }),
      ] },
    ],
    steps: ['Cook the rice.', 'Brown the beef, then stir in soy and chilli paste.', 'Slice the cucumber and onions.', 'Assemble the bowls.'],
    notes: [],
    videos: { youtube: 'https://www.youtube.com/watch?v=demo4' },
  },
  {
    title: 'Egg White Veggie Muffins', source: 2, page: 10, servings: 6,
    kcal: 128, protein: 15, carbs: 5, fat: 5, tags: ['breakfast', 'egg', 'meal prep'],
    blurb: 'Grab-and-go muffins packed with peppers, spinach and feta.',
    groups: [{ name: null, items: [
      I(500, 'ml', 'Egg Whites', A.dairy, { canonical: 'egg white' }),
      I(2, null, 'Eggs', A.dairy, { canonical: 'egg' }),
      I(1, null, 'Bell Pepper', A.produce, { prep: 'diced', canonical: 'bell pepper' }),
      I(60, 'g', 'Baby Spinach', A.produce, { canonical: 'spinach' }),
      I(60, 'g', 'Light Feta', A.dairy, { canonical: 'feta' }),
    ] }],
    steps: ['Heat the oven to 180°C and grease a 12-hole tin.', 'Whisk the egg whites and eggs; season.', 'Divide the veg and feta between the holes, pour over the egg.', 'Bake 20 minutes.'],
    notes: [],
    videos: {},
  },
  {
    title: 'Chicken Tikka Wraps', source: 2, page: 28, servings: 4,
    kcal: 432, protein: 41, carbs: 38, fat: 11, tags: ['main', 'chicken', 'wrap'],
    blurb: 'Yoghurt-marinated chicken, charred under the grill, rolled with crunchy salad.',
    groups: [{ name: null, items: [
      I(700, 'g', 'Chicken Breast', A.meat, { canonical: 'chicken breast' }),
      I(150, 'g', 'Fat-Free Greek Yoghurt', A.dairy, { canonical: 'greek yoghurt' }),
      I(2, 'tbsp', 'Tikka Spice Mix', A.spice, { canonical: 'tikka spice' }),
      I(4, null, 'Wholemeal Wraps', A.grains, { canonical: 'tortilla wrap' }),
      I(1, null, 'Little Gem Lettuce', A.produce, { canonical: 'lettuce' }),
    ] }],
    steps: ['Marinate the chicken in yoghurt and spice for 30 minutes.', 'Grill on high for 12 minutes, turning.', 'Fill the wraps with lettuce and chicken.'],
    notes: [],
    videos: {},
  },
  {
    title: 'Creamy Cajun Chicken Pasta', source: 1, page: 70, servings: 4,
    kcal: 590, protein: 50, carbs: 61, fat: 14, tags: ['main', 'chicken', 'meal prep', 'pasta'],
    blurb: 'A lighter creamy sauce made with light cream cheese and stock.',
    groups: [{ name: null, items: [
      I(800, 'g', 'Chicken Breast', A.meat, { canonical: 'chicken breast' }),
      I(2, 'tsp', 'Cajun Seasoning', A.spice, { canonical: 'cajun seasoning' }),
      I(120, 'g', 'Light Cream Cheese', A.dairy, { canonical: 'cream cheese' }),
      I(300, 'g', 'Penne', A.grains, { canonical: 'pasta' }),
      I(250, 'ml', 'Chicken Stock', A.pantry, { canonical: 'chicken stock' }),
    ] }],
    steps: ['Season and sear the chicken.', 'Add stock and cream cheese and simmer.', 'Stir through cooked penne.'],
    notes: [],
    videos: {},
  },
  {
    title: 'Tuna Sweetcorn Jacket Potatoes', source: 2, page: 34, servings: 2,
    kcal: 410, protein: 36, carbs: 52, fat: 5, tags: ['main', 'potato', 'seafood'],
    blurb: 'Crisp-skinned jackets with a high-protein tuna filling.',
    groups: [{ name: null, items: [
      I(2, null, 'Baking Potatoes', A.produce, { canonical: 'baking potato' }),
      I(2, 'can', 'Tuna in Spring Water', A.pantry, { prep: 'drained', canonical: 'tuna' }),
      I(80, 'g', 'Sweetcorn', A.pantry, { canonical: 'sweetcorn' }),
      I(60, 'g', 'Light Mayo', A.pantry, { canonical: 'mayonnaise' }),
    ] }],
    steps: ['Bake the potatoes at 200°C for an hour.', 'Mix tuna, sweetcorn and mayo.', 'Split the potatoes and fill.'],
    notes: [],
    videos: {},
  },
  {
    title: 'Peri Peri Chicken Burgers', source: 1, page: 77, servings: 4,
    kcal: 455, protein: 43, carbs: 40, fat: 12, tags: ['main', 'chicken', 'burger'],
    blurb: 'Butterflied chicken in a punchy peri peri rub, in toasted brioche.',
    groups: [{ name: null, items: [
      I(4, null, 'Chicken Breasts', A.meat, { prep: 'butterflied', canonical: 'chicken breast' }),
      I(2, 'tbsp', 'Peri Peri Rub', A.spice, { canonical: 'peri peri seasoning' }),
      I(4, null, 'Brioche Buns', A.grains, { canonical: 'burger bun' }),
      I(4, 'slice', 'Light Cheese', A.dairy, { canonical: 'cheese slice' }),
    ] }],
    steps: ['Rub the chicken and grill 5 minutes a side.', 'Toast the buns.', 'Build with cheese and salad.'],
    notes: [],
    videos: { youtube: 'https://www.youtube.com/watch?v=demo5' },
  },
  {
    title: 'Prawn Fried Rice', source: 2, page: 38, servings: 3,
    kcal: 420, protein: 34, carbs: 50, fat: 9, tags: ['main', 'seafood', 'rice'],
    blurb: 'Day-old rice, prawns, peas and egg. Ten minutes in a hot pan.',
    groups: [{ name: null, items: [
      I(300, 'g', 'Raw King Prawns', A.meat, { canonical: 'prawns' }),
      I(450, 'g', 'Cooked Rice', A.grains, { prep: 'cold', canonical: 'cooked rice' }),
      I(2, null, 'Eggs', A.dairy, { canonical: 'egg' }),
      I(120, 'g', 'Frozen Peas', A.produce, { canonical: 'peas' }),
      I(2, 'tbsp', 'Light Soy Sauce', A.pantry, { canonical: 'soy sauce' }),
    ] }],
    steps: ['Scramble the eggs and set aside.', 'Fry the prawns until pink.', 'Add rice and peas, stir-fry 4 minutes, return the egg and season with soy.'],
    notes: [],
    videos: {},
  },
  {
    title: 'Berry Banana Breakfast Smoothie', source: 2, page: 4, servings: 1,
    kcal: 310, protein: 30, carbs: 40, fat: 4, tags: ['breakfast', 'smoothie'],
    blurb: 'Thick enough for a spoon. Use frozen banana for the texture.',
    groups: [{ name: null, items: [
      I(1, null, 'Frozen Banana', A.produce, { canonical: 'banana' }),
      I(80, 'g', 'Frozen Berries', A.produce, { canonical: 'frozen berries' }),
      I(1, 'scoop', 'Vanilla Protein Powder', A.other, { canonical: 'protein powder' }),
      I(200, 'ml', 'Almond Milk', A.dairy, { canonical: 'almond milk' }),
      I(null, null, 'Ice', A.skip, { canonical: 'ice' }),
    ] }],
    steps: ['Blend everything until smooth.'],
    notes: [],
    videos: {},
  },
  {
    title: 'Slow Cooker Beef Ragu', source: 1, page: 84, servings: 6,
    kcal: 530, protein: 45, carbs: 52, fat: 13, tags: ['main', 'beef', 'meal prep', 'pasta'],
    blurb: 'Lean braising steak cooked low and slow until it falls apart.',
    groups: [{ name: null, items: [
      I(1000, 'g', 'Lean Braising Steak', A.meat, { canonical: 'braising steak' }),
      I(2, 'can', 'Chopped Tomatoes', A.pantry, { canonical: 'chopped tomatoes' }),
      I(2, null, 'Carrots', A.produce, { prep: 'diced', canonical: 'carrot' }),
      I(1, null, 'Onion', A.produce, { prep: 'diced', canonical: 'onion' }),
      I(420, 'g', 'Pappardelle', A.grains, { canonical: 'pasta' }),
    ] }],
    steps: ['Brown the beef.', 'Add everything except the pasta to the slow cooker and cook 8 hours on low.', 'Shred the beef and serve over pasta.'],
    notes: ['Freezes well for up to 3 months.'],
    videos: {},
  },
  {
    title: 'Halloumi & Chickpea Grain Bowls', source: 2, page: 48, servings: 3,
    kcal: 495, protein: 28, carbs: 50, fat: 19, tags: ['main', 'bowl', 'meal prep'],
    blurb: 'Golden halloumi, roasted chickpeas, bulgur and a herby dressing.',
    groups: [{ name: null, items: [
      I(225, 'g', 'Light Halloumi', A.dairy, { canonical: 'halloumi' }),
      I(1, 'can', 'Chickpeas', A.pantry, { canonical: 'chickpeas' }),
      I(180, 'g', 'Bulgur Wheat', A.grains, { canonical: 'bulgur wheat' }),
      I(1, 'handful', 'Parsley', A.produce, { canonical: 'parsley' }),
    ] }],
    steps: ['Roast the chickpeas at 200°C for 20 minutes.', 'Cook the bulgur.', 'Fry the halloumi until golden.', 'Assemble with parsley.'],
    notes: [],
    videos: {},
  },
]

function slugify(s) {
  return s.toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

export function buildRecipes() {
  let ingId = 1
  return RAW.map((r, idx) => {
    const id = idx + 1
    const slug = slugify(r.title)
    return {
      id,
      slug,
      title: r.title,
      blurb: r.blurb,
      image_url: `/images/${slug}.svg`,
      palette: PALETTES[idx % PALETTES.length],
      kcal: r.kcal, protein: r.protein, carbs: r.carbs, fat: r.fat,
      servings: r.servings,
      servings_text: r.servings ? `Serves ${r.servings}` : null,
      tags: r.tags,
      source_id: r.source,
      source_page: r.page,
      favourite: idx % 5 === 1,
      videos: r.videos,
      user_edited: false,
      created: idx,
      groups: r.groups.map((g) => ({
        name: g.name,
        note: null,
        items: g.items.map((it) => ({ id: ingId++, ...it })),
      })),
      steps: r.steps,
      notes: r.notes,
    }
  })
}

// SVG "photo": a dish seen from above on a coloured table. Synthetic placeholder, not food photography.
export function placeholderSvg(recipe) {
  const [bg, plate, base, a, b] = recipe?.palette ?? PALETTES[0]
  const seed = recipe ? recipe.id * 37 : 1
  const blobs = []
  for (let i = 0; i < 9; i++) {
    const ang = (seed + i * 71) % 360 * Math.PI / 180
    const rad = 40 + ((seed * (i + 3)) % 120)
    const cx = 400 + Math.cos(ang) * rad
    const cy = 300 + Math.sin(ang) * rad * 0.9
    const r = 26 + ((seed + i * 13) % 34)
    blobs.push(`<circle cx="${cx.toFixed(0)}" cy="${cy.toFixed(0)}" r="${r}" fill="${i % 2 ? a : b}" opacity="0.92"/>`)
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
<rect width="800" height="600" fill="${bg}"/>
<circle cx="400" cy="300" r="250" fill="${plate}"/>
<circle cx="400" cy="300" r="205" fill="${base}"/>
${blobs.join('\n')}
<text x="24" y="580" font-family="sans-serif" font-size="18" fill="#fff" opacity="0.55">synthetic placeholder</text>
</svg>`
}
