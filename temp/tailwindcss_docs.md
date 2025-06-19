# Tailwind CSS Documentation

## Update Default Ring Width and Color in Tailwind v4
DESCRIPTION: Describes the changes to the `ring` utility in Tailwind CSS v4: the default width is now 1px (from 3px) and the default color is `currentColor` (from `blue-500`). The first HTML example shows how to update `ring` to `ring-3` to maintain the previous width. The second HTML example demonstrates adding `ring-blue-500` to explicitly set the color. The CSS example provides theme variables to preserve the v3 default ring width and color behavior, though noting it's for compatibility.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/upgrade-guide.mdx#_snippet_15

LANGUAGE: html
CODE:
```
<button class="focus:ring ..."> <!-- [!code --] -->
<button class="focus:ring-3 ..."> <!-- [!code ++] -->
  <!-- ... -->
</button>
```

LANGUAGE: html
CODE:
```
<button class="focus:ring-3 focus:ring-blue-500 ...">
  <!-- ... -->
</button>
```

LANGUAGE: css
CODE:
```
@theme {
  --default-ring-width: 3px;
  --default-ring-color: var(--color-blue-500);
}
```

---

## Custom Focus Styles with JSX and Tailwind CSS
DESCRIPTION: This JSX snippet demonstrates how to remove the default browser outline using `outline-none` on a `textarea` and apply custom focus styles to its parent container using `focus-within:outline-2` and `focus-within:outline-indigo-600`. It also shows a button with its own `focus:outline` styles, emphasizing the importance of accessibility when removing default outlines.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/outline-style.mdx#_snippet_5

LANGUAGE: jsx
CODE:
```
<div className="mx-auto flex max-w-md flex-col rounded-lg outline-1 outline-gray-300 focus-within:outline-2 focus-within:outline-indigo-600 dark:bg-white/5 dark:outline-transparent dark:focus-within:outline-indigo-500">
  <textarea className="w-full resize-none p-2 outline-none" placeholder="Leave a comment..." />
  <button
    className="mr-2 mb-2 inline-flex items-center self-end rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold text-white shadow-xs hover:bg-indigo-500 focus:outline-2 focus:outline-offset-2 focus:outline-indigo-600"
    type="button"
  >
    Post
  </button>
</div>
```

---

## Adding Viewport Meta Tag in HTML
DESCRIPTION: This snippet demonstrates how to include the viewport meta tag in the <head> of an HTML document. This tag is crucial for proper responsive behavior across different devices, ensuring the page scales correctly.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/responsive-design.mdx#_snippet_2

LANGUAGE: HTML
CODE:
```
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
```

---

## Implementing Floating Labels with Peer and Placeholder-Shown in HTML
DESCRIPTION: This HTML example illustrates how to create a floating label effect using a combination of `peer-*` variants and the new `placeholder-shown` pseudo-class variant. The label's position adjusts based on whether the input has a placeholder shown or is focused, providing a dynamic UI.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/tailwindcss-2-2/index.mdx#_snippet_11

LANGUAGE: HTML
CODE:
```
<div class="relative">
  <input id="name" class="peer ..." />
  <label for="name" class="peer-placeholder-shown:top-4 peer-focus:top-0 ..."> Name </label>
</div>
```

---

## Tailwind CSS v3 to v4 Utility Renames Reference
DESCRIPTION: Provides a comprehensive mapping of renamed utility classes in Tailwind CSS v4, including changes to shadow, drop-shadow, blur, backdrop-blur, rounded, outline, and ring utilities, to ensure consistency and predictability.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/upgrade-guide.mdx#_snippet_6

LANGUAGE: APIDOC
CODE:
```
v3             | v4
---------------|---------------
shadow-sm      | shadow-xs
shadow         | shadow-sm
drop-shadow-sm | drop-shadow-xs
drop-shadow    | drop-shadow-sm
blur-sm        | blur-xs
blur           | blur-sm
backdrop-blur-sm | backdrop-blur-xs
backdrop-blur  | backdrop-blur-sm
rounded-sm     | rounded-xs
rounded        | rounded-sm
outline-none   | outline-hidden
ring           | ring-3
```

---

## Defining Container Query Ranges with Tailwind CSS
DESCRIPTION: This snippet demonstrates how to combine `@min-*` and `@max-*` variants to create container query ranges. The `@min-md:@max-xl:hidden` utility hides the element only when the container's width is between the 'md' and 'xl' breakpoints, providing fine-grained control over responsiveness.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/tailwindcss-v4/index.mdx#_snippet_18

LANGUAGE: HTML
CODE:
```
<div class="@container">
  <div class="flex @min-md:@max-xl:hidden">
    <!-- ... -->
  </div>
</div>
```

---

## Mapping Props to Static Class Name Variants in JSX with Tailwind
DESCRIPTION: This JSX code further illustrates the best practice of mapping component props to complete, static Tailwind class names. This approach allows for flexible styling, such as applying different color shades or text colors based on a single prop, while ensuring all class names are detectable by Tailwind's plain-text scanner.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/detecting-classes-in-source-files.mdx#_snippet_5

LANGUAGE: JSX
CODE:
```
function Button({ color, children }) {
  const colorVariants = {
    blue: "bg-blue-600 hover:bg-blue-500 text-white",
    red: "bg-red-500 hover:bg-red-400 text-white",
    yellow: "bg-yellow-300 hover:bg-yellow-400 text-black"
  };

  return <button className={`${colorVariants[color]} ...`}>{children}</button>;
}
```

---

## Applying Tailwind CSS State Variants to Input (HTML)
DESCRIPTION: This HTML snippet showcases the direct application of Tailwind CSS utility classes with pseudo-class variants (`invalid`, `focus`, `disabled`, `dark:disabled`) to an `<input>` element. It highlights how these variants automatically apply styles based on the input's state, simplifying template logic and reducing the need for manual conditional styling.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/hover-focus-and-other-states.mdx#_snippet_11

LANGUAGE: HTML
CODE:
```
<input
  type="text"
  value="tbone"
  disabled
  class="invalid:border-pink-500 invalid:text-pink-600 focus:border-sky-500 focus:outline focus:outline-sky-500 focus:invalid:border-pink-500 focus:invalid:outline-pink-500 disabled:border-gray-200 disabled:bg-gray-50 disabled:text-gray-500 disabled:shadow-none dark:disabled:border-gray-700 dark:disabled:bg-gray-800/20 ..."
/>
```

---

## Applying Hover Background Color with Tailwind CSS (HTML)
DESCRIPTION: This snippet demonstrates how to apply a different background color on hover using Tailwind CSS utility classes. The hover:bg-fuchsia-500 class changes the button's background to fuchsia when the user hovers over it, while bg-indigo-500 sets the default background.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/background-color.mdx#_snippet_2

LANGUAGE: html
CODE:
```
<!-- [!code classes:hover:bg-fuchsia-500] -->
<button class="bg-indigo-500 hover:bg-fuchsia-500 ...">Save changes</button>
```

---

## Applying Dynamic Data Attribute Variants - HTML
DESCRIPTION: This HTML snippet illustrates the ability to target custom boolean data attributes dynamically in Tailwind CSS v4.0. The `data-current:opacity-100` variant applies styles when the `data-current` attribute is present, removing the need for explicit variant configuration.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/tailwindcss-v4/index.mdx#_snippet_14

LANGUAGE: HTML
CODE:
```
<div data-current class="opacity-75 data-current:opacity-100">
  <!-- ... -->
</div>
```

---

## Creating Dynamic Dialog Transitions with Headless UI and React
DESCRIPTION: This example illustrates how to implement a dialog with distinct enter and leave transition styles using stacked data attributes. It uses `data-[closed]:data-[enter]:-translate-x-8` for entering from the left and `data-[closed]:data-[leave]:translate-x-8` for leaving to the right, showcasing advanced transition control.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/2024-06-21-headless-ui-v2-1/index.mdx#_snippet_1

LANGUAGE: jsx
CODE:
```
import { Dialog } from "@headlessui/react";
import { useState } from "react";

function Example() {
  let [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button onClick={() => setIsOpen(true)}>Open dialog</button>
      <Dialog
        open={isOpen}
        onClose={() => setIsOpen(false)}
        // [!code highlight:8]
        transition
        className={`
          transition duration-300 ease-out
          data-[closed]:opacity-0
          data-[closed]:data-[enter]:-translate-x-8
          data-[closed]:data-[leave]:translate-x-8
        `}
      >
        {/* Dialog content… */}
      </Dialog>
    </>
  );
}
```

---

## Importing Tailwind CSS v4.0 in CSS
DESCRIPTION: This CSS line imports the entire Tailwind CSS framework into a project's stylesheet. In v4.0, this single @import rule replaces the previous @tailwind directives, streamlining the process of including Tailwind's base styles, components, and utilities.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/tailwindcss-v4/index.mdx#_snippet_6

LANGUAGE: CSS
CODE:
```
@import "tailwindcss";
```

---

## Configuring @tailwindcss/forms Plugin (JavaScript)
DESCRIPTION: This JavaScript snippet demonstrates how to include the @tailwindcss/forms plugin in the tailwind.config.js file. Adding this line to the plugins array enables the plugin's base styles, allowing form elements to be easily styled with utility classes. This is a prerequisite for the utility-friendly form styling.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/tailwindcss-v2/index.mdx#_snippet_13

LANGUAGE: JavaScript
CODE:
```
module.exports = {
  // ...
  plugins: [require("@tailwindcss/forms")],
};
```

---

## Building a Responsive Component with Tailwind Utility Classes
DESCRIPTION: This example demonstrates a fully responsive UI component built entirely with Tailwind CSS utility classes. It showcases how to apply styles for different screen sizes, as well as interactive states like hover and active, without writing custom CSS.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/styling-with-utility-classes.mdx#_snippet_2

LANGUAGE: jsx
CODE:
```
<div className="mx-auto max-w-sm space-y-2 rounded-xl bg-white px-8 py-8 shadow-lg ring ring-black/5 @sm:flex @sm:items-center @sm:space-y-0 @sm:gap-x-6 @sm:py-4">
      <img
        className="mx-auto block h-24 rounded-full @sm:mx-0 @sm:shrink-0"
        src={erinLindford.src}
        alt="Woman's Face"
      />
      <div className="space-y-2 text-center @sm:text-left">
        <div className="space-y-0.5">
          <p className="text-lg font-semibold text-black">Erin Lindford</p>
          <p className="font-medium text-gray-500">Product Engineer</p>
        </div>
        <button className="rounded-full border border-purple-200 px-4 py-1 text-sm font-semibold text-purple-600 hover:border-transparent hover:bg-purple-600 hover:text-white active:bg-purple-700">
          Message
        </button>
      </div>
    </div>
```

LANGUAGE: html
CODE:
```
<!-- [!code classes:sm:flex-row,sm:py-4,sm:gap-6,sm:mx-0,sm:shrink-0,sm:text-left,sm:items-center] -->
<!-- [!code classes:hover:text-white,hover:bg-purple-600,hover:border-transparent,active:bg-purple-700] -->
<div class="flex flex-col gap-2 p-8 sm:flex-row sm:items-center sm:gap-6 sm:py-4 ...">
  <img class="mx-auto block h-24 rounded-full sm:mx-0 sm:shrink-0" src="/img/erin-lindford.jpg" alt="" />
  <div class="space-y-2 text-center sm:text-left">
    <div class="space-y-0.5">
      <p class="text-lg font-semibold text-black">Erin Lindford</p>
      <p class="font-medium text-gray-500">Product Engineer</p>
    </div>
    <!-- prettier-ignore -->
    <button class="border-purple-200 text-purple-600 hover:border-transparent hover:bg-purple-600 hover:text-white active:bg-purple-700 ...">
      Message
    </button>
  </div>
</div>
```

---

## Applying Responsive Width Utilities in HTML
DESCRIPTION: This HTML snippet illustrates how to apply responsive width utility classes using Tailwind CSS. By default, the image has a width of w-16, which changes to md:w-32 on medium screens and lg:w-48 on large screens, showcasing conditional styling based on breakpoints.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/responsive-design.mdx#_snippet_3

LANGUAGE: HTML
CODE:
```
<img class="w-16 md:w-32 lg:w-48" src="..." />
```

---

## Using Dynamic Grid Column Utilities - HTML
DESCRIPTION: This HTML snippet demonstrates the enhanced flexibility of Tailwind CSS v4.0, allowing dynamic values for utilities like `grid-cols-*`. Users can now specify arbitrary column counts (e.g., `grid-cols-15`) without prior configuration, simplifying grid layout creation.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/tailwindcss-v4/index.mdx#_snippet_13

LANGUAGE: HTML
CODE:
```
<div class="grid grid-cols-15">
  <!-- ... -->
</div>
```

---

## Creating a Composable Text Field with Catalyst (JSX)
DESCRIPTION: This example illustrates how to create a text field using Catalyst's HTML-mirrored API. It utilizes separate, composable components like `Field`, `Label`, `Description`, and `Input` to build the form element. This design allows for greater flexibility in styling and rearranging individual parts of the field.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/introducing-catalyst/index.mdx#_snippet_3

LANGUAGE: jsx
CODE:
```
import { Description, Field, Label } from "@/components/fieldset";
import { Input } from "@/components/input";

function Example() {
  return (
    <Field>
      <Label>Product name</Label>
      <Description>Use the name you'd like people to see in their cart.</Description>
      <Input name="product_name" />
    </Field>
  );
}
```

---

## Defining Custom Theme Variables with @theme in CSS
DESCRIPTION: This CSS snippet shows how to define custom theme values like font families, breakpoints, and colors directly within a main.css file using the @theme directive. These CSS variables replace the need for a JavaScript configuration file, making Tailwind CSS feel more CSS-native.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/tailwindcss-v4-alpha/index.mdx#_snippet_4

LANGUAGE: css
CODE:
```
/* [!code filename:main.css] */
@import "tailwindcss";

@theme {
  --font-family-display: "Satoshi", "sans-serif";

  --breakpoint-3xl: 1920px;

  --color-neon-pink: oklch(71.7% 0.25 360);
  --color-neon-lime: oklch(91.5% 0.258 129);
  --color-neon-cyan: oklch(91.3% 0.139 195.8);
}
```

---

## Applying Responsive Container Max Width in Tailwind CSS
DESCRIPTION: Defines a responsive container that sets its width to 100% by default and applies increasing maximum widths at different breakpoint sizes (40rem, 48rem, 64rem, 80rem, 96rem). This ensures content is constrained on larger screens.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/max-width.mdx#_snippet_28

LANGUAGE: CSS
CODE:
```
width: 100%;
@media (width >= 40rem) { max-width: 40rem; }
@media (width >= 48rem) { max-width: 48rem; }
@media (width >= 64rem) { max-width: 64rem; }
@media (width >= 80rem) { max-width: 80rem; }
@media (width >= 96rem) { max-width: 96rem; }
```

---

## Implementing Menu Transitions with Headless UI and React
DESCRIPTION: This snippet demonstrates how to apply transitions to a Headless UI `MenuItems` component using the new `transition` prop and data attributes. It shows how to define different styles for closed, entering, and leaving states using Tailwind CSS classes like `data-[closed]:scale-95` and `data-[enter]:duration-200`.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/blog/2024-06-21-headless-ui-v2-1/index.mdx#_snippet_0

LANGUAGE: jsx
CODE:
```
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";

function Example() {
  return (
    <Menu>
      <MenuButton>My account</MenuButton>
      <MenuItems
        // [!code highlight:7]
        transition
        className={`
          transition ease-out
          data-[closed]:scale-95 data-[closed]:opacity-0
          data-[enter]:duration-200 data-[leave]:duration-300
        `}
      >
        {/* Menu items… */}
      </MenuItems>
    </Menu>
  );
}
```

---

## Styling Direct Children with Tailwind CSS `*` Variant
DESCRIPTION: This example illustrates the use of the `*` variant in Tailwind CSS to apply styles directly to all immediate child elements. This is particularly useful when you cannot directly modify the child elements, allowing you to apply common styles like `rounded-full`, `border`, and background colors to all `<li>` items within the `<ul>`.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/hover-focus-and-other-states.mdx#_snippet_89

LANGUAGE: html
CODE:
```
<!-- [!code classes:*:rounded-full] -->
<!-- [!code classes:*:border] -->
<!-- [!code classes:*:border-sky-100] -->
<!-- [!code classes:*:bg-sky-50] -->
<!-- [!code classes:*:px-2] -->
<!-- [!code classes:*:py-0.5] -->
<!-- [!code classes:dark:text-sky-300] -->
<!-- [!code classes:dark:*:border-sky-500/15] -->
<!-- [!code classes:dark:*:bg-sky-500/10] -->
<div>
  <h2>Categories<h2>
  <ul class="*:rounded-full *:border *:border-sky-100 *:bg-sky-50 *:px-2 *:py-0.5 dark:text-sky-300 dark:*:border-sky-500/15 dark:*:bg-sky-500/10 ...">
    <li>Sales</li>
    <li>Marketing</li>
    <li>SEO</li>
    <!-- ... -->
  </ul>
</div>
```

---

## Applying Responsive Grid Layouts with Tailwind CSS HTML
DESCRIPTION: This snippet demonstrates how to create a responsive grid layout using Tailwind CSS's responsive breakpoints. It shows how to define different column counts for mobile (grid-cols-3), medium screens (md:grid-cols-4), and large screens (lg:grid-cols-6).
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/hover-focus-and-other-states.mdx#_snippet_48

LANGUAGE: html
CODE:
```
<div class="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
  <!-- ... -->
</div>
```

---

## Unstyling Heading Elements in Preflight CSS
DESCRIPTION: This Preflight CSS rule unstyles all heading elements (`h1` through `h6`), setting their `font-size` and `font-weight` to `inherit`. This approach prevents accidental deviation from the defined type scale and encourages conscious styling of headings using Tailwind's utility classes.
SOURCE: https://github.com/tailwindlabs/tailwindcss.com/blob/main/src/docs/preflight.mdx#_snippet_4

LANGUAGE: CSS
CODE:
```
h1,
h2,
h3,
h4,
h5,
h6 {
  font-size: inherit;
  font-weight: inherit;
}
