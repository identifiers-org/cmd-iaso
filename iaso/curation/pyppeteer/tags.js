class IasoTagSelector {
  constructor(identifier, tags=[], onupdate=null) {
    this.identifier = identifier;

    this.selector = document.createElement("div");
    this.selector.classList.add("iaso-informant-overlay-tag-selector");
    this.selector.innerHTML = '<span class="iaso-informant-overlay-tag-spacer"></span>';
    this.selector.onclick = e => e.stopPropagation();

    this.onupdate = onupdate;

    this.update(tags, tags.length, false);

    return this.selector;
  }

  createTagElement(text, index) {
    const tag = document.createElement("div");
    tag.classList.add("iaso-informant-overlay-tag-item");
    tag.onclick = e => {
      e.stopPropagation();

      const value = this.ref.value
                    .replace(this.delimeter, "")
                    .trim();

      let tags = [...this.tags];

      if (index < this.index) {
        if (value.length > 0 && !this.tags.includes(value)) {
          tags.splice(this.index, 0, value);
        }

        this.ref.value = tags[index];
        tags.splice(index, 1);
      } else {
        this.ref.value = tags[index];
        tags.splice(index, 1);

        if (value.length > 0 && !this.tags.includes(value)) {
          tags.splice(this.index, 0, value);
          index += 1;
        }
      }

      this.update(tags, index);
    };
    tag.innerHTML = `
      <span class="iaso-informant-overlay-tag-text" data-content="${text}">${text}</span>
      <i class="iaso-informant-overlay-tag-remove"/>
    `;

    tag.children[1].onclick = e => {
      e.stopPropagation();
      let tags = [...this.tags];
      tags.splice(index, 1);
      this.update(tags, (index < this.index) ? (this.index - 1) : this.index);
    };

    return tag;
  }

  update(tags, index, focus=true) {
    this.tags = tags;
    this.index = index;

    console.info(`iaso-informant-tags-${this.identifier}-${JSON.stringify(this.tags)}`);

    if (this.onupdate !== null) {
        this.onupdate(tags);
    }

    const prevValue = this.ref ? this.ref.value : "";

    this.selector.innerHTML = '<span class="iaso-informant-overlay-tag-spacer"></span>';

    for (let index = 0; index < this.index; index++) {
      this.selector.appendChild(this.createTagElement(this.tags[index], index));
    }

    this.ref = document.createElement("input");
    this.ref.setAttribute("type", "text");
    this.ref.classList.add("iaso-informant-overlay-tag-input");
    this.ref.style = "box-shadow: none; height: auto !important";
    this.ref.value = prevValue;
    this.ref.addEventListener("keydown", this.handleTagsKeyDown);
    const oldRefOnClick = this.ref.onclick;
    this.ref.onclick = e => e.stopPropagation();
    this.selector.appendChild(this.ref);

    for (let index = this.index; index < this.tags.length; index++) {
      this.selector.appendChild(this.createTagElement(this.tags[index], index));
    }

    if (focus) {
        this.ref.focus();
    }
  }

  removeTagToEdit() {
    if (this.ref.value.length > 0 || this.index <= 0) {
      return false;
    }

    let tags = [...this.tags];
    this.ref.value = tags.splice(this.index - 1, 1)[0] + " ";
    this.update(tags, this.index - 1);

    return true;
  }

  addTagToList(cursor) {
    let [left, right] = [
      this.ref.value
        .slice(0, cursor)
        .replace(this.delimeter, "")
        .trim(),
      this.ref.value
        .slice(cursor, this.ref.value.length)
        .replace(this.delimeter, "")
        .trim(),
    ];

    this.ref.value = "";

    setTimeout(() => (this.ref.selectionStart = this.ref.selectionEnd = 0), 0);

    if (left.length <= 0 && right.length <= 0) {
      return false;
    }

    if (left.length <= 0) {
      if (this.tags.includes(right)) {
        return true;
      }

      let tags = [...this.tags];
      tags.splice(this.index, 0, right);
      this.update(tags, this.index);

      return true;
    }

    this.ref.value = right;

    if (this.tags.includes(left)) {
      return true;
    }

    let tags = [...this.tags];
    tags.splice(this.index, 0, left);
    this.update(tags, this.index + 1);

    return true;
  }

  handleTagsKeyDown = e => {
    let cursor =
      this.ref.selectionDirection === "backward"
        ? this.ref.selectionEnd
        : this.ref.selectionStart;

    if (e.key === "Backspace") {
      this.removeTagToEdit();
    } else if (e.key === "Enter") {
      this.addTagToList(cursor);
    } else if (e.key === "," || e.key === ";") {
      this.addTagToList(cursor);

      e.preventDefault();
    } else if (e.key === "Tab") {
      if (this.addTagToList(cursor)) {
        e.preventDefault();
      } else {
        this.update(this.tags, this.tags.length);
      }
    } else if (e.key === "ArrowLeft" && this.index > 0 && cursor <= 0) {
      let value = this.ref.value.replace(this.delimeter, "").trim();

      let tags = [...this.tags];
      let index = this.index - 1;

      if (value.length > 0 && !this.tags.includes(value)) {
        tags.splice(this.index, 0, value);
        index = this.index;

        e.preventDefault();
      }

      this.ref.value = "";

      this.update(tags, index);
    } else if (
      e.key === "ArrowRight" &&
      this.index < this.tags.length &&
      cursor >= this.ref.value.length
    ) {
      let value = this.ref.value.replace(this.delimeter, "").trim();

      let tags = [...this.tags];

      if (value.length > 0 && !this.tags.includes(value)) {
        tags.splice(this.index, 0, value);

        e.preventDefault();
      }

      this.ref.value = "";

      this.update(tags, this.index + 1);
    }
  };
}
