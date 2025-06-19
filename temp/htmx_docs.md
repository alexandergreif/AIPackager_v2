# HTMX Documentation

## Include htmx and create a POST button
DESCRIPTION: This snippet demonstrates how to include the htmx library and create a button that sends a POST request to the '/clicked' endpoint when clicked. The `hx-swap` attribute specifies that the entire button should be replaced with the response from the server.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/README.md#_snippet_0

LANGUAGE: html
CODE:
```
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <!-- have a button POST a click via AJAX -->
  <button hx-post="/clicked" hx-swap="outerHTML">
    Click Me
  </button>
```

---

## Including htmx via CDN
DESCRIPTION: This code snippet demonstrates how to include htmx 2.0.0 in an HTML file using a CDN. The script tag references the minified version of htmx hosted on unpkg.com. This method allows users to quickly add htmx to their projects without needing to download or manage the library locally.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/posts/2024-06-17-htmx-2.0.0-is-released.md#_snippet_0

LANGUAGE: html
CODE:
```
<script src="https://unpkg.com/htmx.org@2.0.0/dist/htmx.min.js"></script>
```

---

## Implementing AJAX Request with htmx
DESCRIPTION: This code snippet demonstrates an AJAX request implementation using htmx. The `hx-get` attribute on the button element specifies the URL to which the request is sent when the button is clicked. The behavior of the button is immediately obvious upon inspection, exemplifying good Locality of Behaviour (LoB).
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/essays/locality-of-behaviour.md#_snippet_0

LANGUAGE: html
CODE:
```
<button hx-get="/clicked">Click Me</button>
```

---

## Defining Web Component with HTMX Integration in JS
DESCRIPTION: Defines a custom web component (`my-component`) using `customElements.define`. Inside the `connectedCallback`, a shadow DOM is attached, and HTML content with HTMX attributes (`hx-get`, `hx-target`) is added.  `htmx.process(root)` is called to inform HTMX about the shadow DOM, enabling HTMX to work within the component. The mode is set to 'closed' which means that the shadow DOM is not accessible from JavaScript outside the component.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/examples/web-components.md#_snippet_0

LANGUAGE: JavaScript
CODE:
```
customElements.define('my-component', class MyComponent extends HTMLElement {
  // This method runs when your custom element is added to the page
  connectedCallback() {
    const root = this.attachShadow({ mode: 'closed' })
    root.innerHTML = `
      <button hx-get="/my-component-clicked" hx-target="next div">Click me!</button>
      <div></div>
    `
    htmx.process(root) // Tell HTMX about this component's shadow DOM
  }
})
```

---

## GET Request with hx-get in htmx
DESCRIPTION: This HTML snippet demonstrates how to use the `hx-get` attribute to trigger a GET request to the `/example` endpoint when the button is clicked. The HTML returned from the server will be swapped into the `innerHTML` of the button element. No specific dependencies are required beyond the htmx library itself.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/attributes/hx-get.md#_snippet_0

LANGUAGE: HTML
CODE:
```
  <button hx-get="/example">Get Some HTML</button>
```

---

## Async Auth Token Handling with htmx Events
DESCRIPTION: This JavaScript snippet manages asynchronous authentication tokens and integrates them with htmx requests. It listens for the htmx:confirm event to delay requests until the auth promise resolves. It adds the authentication token as a header to each request using the htmx:configRequest event.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/examples/async-auth.md#_snippet_1

LANGUAGE: JavaScript
CODE:
```
<script>
  // auth is a promise returned by our authentication system

  // await the auth token and store it somewhere
  let authToken = null;
  auth.then((token) => {
    authToken = token
  })

  // gate htmx requests on the auth token
  htmx.on("htmx:confirm", (e)=> {
    // if there is no auth token
    if(authToken == null) {
      // stop the regular request from being issued
      e.preventDefault()
      // only issue it once the auth promise has resolved
      auth.then(() => e.detail.issueRequest())
    }
  })

  // add the auth token to the request as a header
  htmx.on("htmx:configRequest", (e)=> {
    e.detail.headers["AUTH"] = authToken
  })
</script>
```

---

## Basic hx-swap-oob Example HTML
DESCRIPTION: This example demonstrates a basic use case of `hx-swap-oob`. The first `div` will be swapped into the target element. The second `div` with `hx-swap-oob="true"` will replace the element with the id `alerts` in the DOM.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/attributes/hx-swap-oob.md#_snippet_0

LANGUAGE: html
CODE:
```
<div>
 ...
</div>
<div id="alerts" hx-swap-oob="true">
    Saved!
</div>
```

---

## Modifying HTMX Request Parameters - JavaScript
DESCRIPTION: This JavaScript snippet shows how to use the `htmx:configRequest` event to dynamically add or update parameters and headers before an htmx AJAX request is sent. It allows for injecting data like authentication tokens into the request payload. The event's `detail.parameters` object can be modified to include new key-value pairs.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/events.md#_snippet_1

LANGUAGE: JavaScript
CODE:
```
document.body.addEventListener('htmx:configRequest', function(evt) {
    evt.detail.parameters['auth_token'] = getAuthToken(); // add a new parameter into the mix
});
```

---

## Processing New Content with htmx.process()
DESCRIPTION: This JavaScript snippet demonstrates using `htmx.process()` after dynamically adding content to the DOM to ensure that htmx attributes within the new content are processed. This snippet uses the `fetch` API to load HTML content from a server, then sets the inner HTML of an element with the ID 'my-div', and finally calls `htmx.process()` on that element.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/docs.md#_snippet_53

LANGUAGE: javascript
CODE:
```
let myDiv = document.getElementById('my-div')
fetch('http://example.com/movies.json')
    .then(response => response.text())
    .then(data => { myDiv.innerHTML = data; htmx.process(myDiv); } );
```

---

## HTML Form and Contacts Table
DESCRIPTION: This HTML snippet presents a form for adding contacts and a table to display the current list of contacts. It demonstrates a typical structure for a web page where users can input data and view existing data.  The form submits to `/contacts` via POST.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/essays/hypermedia-apis-vs-data-apis.md#_snippet_2

LANGUAGE: html
CODE:
```
<div>
    <form action='/contacts' method="post">
      <!-- form for adding contacts -->
    </form>
    <table>
      <!-- contacts table -->
    </table>
</div>
```

---

## htmx Select Elements
DESCRIPTION: This HTML snippet defines two select elements, 'make' and 'model'. The 'make' select uses hx-get to make a GET request to the '/models' endpoint when its value changes, updating the 'model' select with the response.  The hx-indicator attribute displays a loading indicator during the request.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/examples/value-select.md#_snippet_0

LANGUAGE: html
CODE:
```
<div>
    <label >Make</label>
    <select name="make" hx-get="/models" hx-target="#models" hx-indicator=".htmx-indicator">
      <option value="audi">Audi</option>
      <option value="toyota">Toyota</option>
      <option value="bmw">BMW</option>
    </select>
  </div>
  <div>
    <label>Model</label>
    <select id="models" name="model">
      <option value="a1">A1</option>
      ...
    </select>
    <img class="htmx-indicator" width="20" src="/img/bars.svg">
</div>
```

---

## Triggering AJAX on Input Change with Delay - HTML
DESCRIPTION: This example shows how to trigger an AJAX GET request to '/search' on input change, but only if the value has changed and after a 1-second delay. This is useful for search boxes. The hx-target attribute specifies that the response should be appended to the div with the id 'search-results'.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/attributes/hx-trigger.md#_snippet_4

LANGUAGE: html
CODE:
```
<input name="q"
       hx-get="/search" hx-trigger="input changed delay:1s"
       hx-target="#search-results"/>
```

---

## htmx: Button with AJAX POST Request
DESCRIPTION: This HTML snippet demonstrates a basic htmx example: a button that, when clicked, sends an AJAX POST request to the '/clicked' endpoint. The `hx-swap="outerHTML"` attribute specifies that the entire button element should be replaced with the HTML response from the server.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/_index.md#_snippet_2

LANGUAGE: HTML
CODE:
```
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <!-- have a button POST a click via AJAX -->
  <button hx-post="/clicked" hx-swap="outerHTML">
    Click Me
  </button>
```

---

## htmx Target Attribute Example
DESCRIPTION: This HTML snippet shows the usage of the `hx-target` attribute to specify where the response from an htmx request should be loaded. In this case, the response from the `/trigger_delay` endpoint will be loaded into the element with the ID `search-results`. The request is triggered on `keyup` with a delay of 500ms and only if the value has changed.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/docs.md#_snippet_19

LANGUAGE: html
CODE:
```
<input type="text" name="q"
    hx-get="/trigger_delay"
    hx-trigger="keyup delay:500ms changed"
    hx-target="#search-results"
    placeholder="Search...">
<div id="search-results"></div>
```

---

## Editable Table Row with HTMX Actions
DESCRIPTION: This HTML snippet defines the editable table row with input fields for name and email. It includes HTMX attributes for handling the 'cancel' event, sending a GET request to revert to the read-only state, and a PUT request to save the changes. hx-include is used to include the input values in the PUT request.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/examples/edit-row.md#_snippet_2

LANGUAGE: html
CODE:
```
<tr hx-trigger='cancel' class='editing' hx-get="/contact/${contact.id}">
  <td><input autofocus name='name' value='${contact.name}'></td>
  <td><input name='email' value='${contact.email}'></td>
  <td>
    <button class="btn danger" hx-get="/contact/${contact.id}">
      Cancel
    </button>
    <button class="btn danger" hx-put="/contact/${contact.id}" hx-include="closest tr">
      Save
    </button>
  </td>
</tr>
```

---

## Converting hx-on attributes to hx-on:
DESCRIPTION: Demonstrates the syntax change for event handling in htmx 2.x. The `hx-on` attribute is replaced with `hx-on:` followed by the kebab-case version of the event name. This example shows a button with event listeners for `htmx:beforeRequest` and `htmx:afterRequest`.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/migration-guide-htmx-1.md#_snippet_0

LANGUAGE: HTML
CODE:
```
     <button hx-get="/info" hx-on="htmx:beforeRequest: alert('Making a request!')
                                   htmx:afterRequest: alert('Done making a request!')">
      Get Info!
     </button>
```

LANGUAGE: HTML
CODE:
```
     <button hx-get="/info" hx-on:htmx:before-request="alert('Making a request!')"
                            hx-on:htmx:after-request="alert('Done making a request!')">
      Get Info!
     </button>
```

---

## htmx Installation via CDN
DESCRIPTION: This code snippet shows how to include htmx in an HTML page using a CDN.  It includes a specific version of htmx from unpkg.com. The `integrity` attribute is used for Subresource Integrity (SRI) to ensure the file hasn't been tampered with.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/docs.md#_snippet_3

LANGUAGE: HTML
CODE:
```
<script src="https://unpkg.com/htmx.org@2.0.4" integrity="sha384-HGfztofotfshcF7+8n44JQL2oJmowVChPTg48S+jvZoztPfvwD79OC/LTtG6dMp+" crossorigin="anonymous"></script>
```

---

## JavaScript HTML escaping function
DESCRIPTION: This JavaScript function, `escapeHtmlText`, escapes HTML characters to prevent XSS vulnerabilities. It replaces characters like `<`, `>`, `&`, `"`, `'`, `/`, `` ` ``, and `=` with their corresponding HTML entities.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/essays/web-security-basics-with-htmx.md#_snippet_4

LANGUAGE: JavaScript
CODE:
```
/**
 * Replace any characters that could be used to inject a malicious script in an HTML context.
 */
export function escapeHtmlText (value) {
  const stringValue = value.toString()
  const entityMap = {
    '&': '&',
    '<': '<',
    '>': '>',
    '"': '"',
    "'": '&#x27;',
    '/': '&#x2F;',
    '`': '&grave;',
    '=': '&#x3D;'
  }

  // Match any of the characters inside /[ ... ]/
  const regex = /[&<>"'`=/]/g
  return stringValue.replace(regex, match => entityMap[match])
}
```

---

## Validating URLs with the htmx:validateUrl Event
DESCRIPTION: This JavaScript snippet demonstrates using the `htmx:validateUrl` event to validate URLs before htmx issues a request. It adds an event listener to the body that checks if the request is to the same host or to 'myserver.com'. If not, it prevents the default action to block the request.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/docs.md#_snippet_56

LANGUAGE: javascript
CODE:
```
document.body.addEventListener('htmx:validateUrl', function (evt) {
  // only allow requests to the current server as well as myserver.com
  if (!evt.detail.sameHost && evt.detail.url.hostname !== "myserver.com") {
    evt.preventDefault();
  }
});
```

---

## Initializing SortableJS with htmx.onLoad
DESCRIPTION: This JavaScript snippet shows how to initialize SortableJS using htmx's `htmx.onLoad` function, ensuring initialization after new content is loaded via htmx. The `content` parameter in `htmx.onLoad` represents the newly loaded portion of the DOM. This is important to only apply the sortable functionality to the new content that has been loaded via htmx.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/docs.md#_snippet_52

LANGUAGE: javascript
CODE:
```
htmx.onLoad(function(content) {
    var sortables = content.querySelectorAll(".sortable");
    for (var i = 0; i < sortables.length; i++) {
        var sortable = sortables[i];
        new Sortable(sortable, {
            animation: 150,
            ghostClass: 'blue-background-class'
        });
    }
})
```

---

## Basic hx-swap Example
DESCRIPTION: This code snippet demonstrates the basic usage of the `hx-swap` attribute to append the content received from `/example` after the `div` element. It showcases how to trigger an AJAX request using `hx-get` and specify the swap strategy.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/attributes/hx-swap.md#_snippet_0

LANGUAGE: html
CODE:
```
  <div hx-get="/example" hx-swap="afterend">Get Some HTML & Append It</div>
```

---

## htmx Button Example
DESCRIPTION: This HTML snippet demonstrates how to use htmx to load content into an element. When the button is clicked, it sends a GET request to `/ajax/test.html` and loads the response into the element with the ID `result`. It requires the htmx library to function correctly.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/essays/htmx-sucks.md#_snippet_1

LANGUAGE: HTML
CODE:
```
<button hx-get="/ajax/test.html"
        hx-target="#result">
    Load
</button>
```

---

## Display Contact Details with HTMX
DESCRIPTION: This HTML snippet displays the contact details and includes a button that, when clicked, fetches the editing UI from the `/contact/1/edit` endpoint using an HTMX GET request. The `hx-target` attribute specifies that the response should replace the current div, and `hx-swap` dictates the `outerHTML` should be replaced.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/examples/click-to-edit.md#_snippet_0

LANGUAGE: html
CODE:
```
<div hx-target="this" hx-swap="outerHTML">
    <div><label>First Name</label>: Joe</div>
    <div><label>Last Name</label>: Blow</div>
    <div><label>Email</label>: joe@blow.com</div>
    <button hx-get="/contact/1/edit" class="btn primary">
    Click To Edit
    </button>
</div>
```

---

## htmx Request Indicator
DESCRIPTION: This HTML snippet shows how to use the `htmx-indicator` class to display a spinner during an AJAX request. The `htmx-request` class is added to the button during the request, revealing the image with the `htmx-indicator` class.  It requires a spinner image file at `/spinner.gif`
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/docs.md#_snippet_16

LANGUAGE: html
CODE:
```
<button hx-get="/click">
    Click Me!
    <img class="htmx-indicator" src="/spinner.gif">
</button>
```

---

## htmx Installation via npm
DESCRIPTION: This command demonstrates how to install htmx as a dependency using npm.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/docs.md#_snippet_6

LANGUAGE: Shell
CODE:
```
npm install htmx.org@2.0.4
```

---

## Using hx-select with htmx
DESCRIPTION: This code snippet demonstrates how to use the `hx-select` attribute in htmx to select a specific element from the response of a GET request and swap it into the DOM. The `hx-get` attribute triggers a GET request to `/info`. The `hx-select` attribute specifies the CSS selector `#info-detail` to select the element with the id `info-detail` from the response. The `hx-swap` attribute is set to `outerHTML`, which replaces the entire button element with the selected content.
SOURCE: https://github.com/bigskysoftware/htmx/blob/master/www/content/attributes/hx-select.md#_snippet_0

LANGUAGE: HTML
CODE:
```
<div>
    <button hx-get="/info" hx-select="#info-detail" hx-swap="outerHTML">
        Get Info!
    </button>
</div>
