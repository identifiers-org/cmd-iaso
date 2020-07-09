function(xpath) {
    const handle = document.evaluate(
        xpath, // xpathExpression
        document, // contextNode
        null, // namespaceResolver
        XPathResult.FIRST_ORDERED_NODE_TYPE, // resultType
        null // result
    ).singleNodeValue;

    const editButton = handle
        .parentNode.parentNode.parentNode
        .parentNode.parentNode.previousSibling
        .firstChild.firstChild;

    editButton.scrollIntoView();
    window.scrollBy(0, -54);
    editButton.click();
}
