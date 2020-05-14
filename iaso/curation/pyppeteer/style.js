async function (content, id) {
    if (document.getElementById(id) !== null) {
        return;
    }
    
    const style = document.createElement('style');
    
    style.type = 'text/css';
    style.id = id;
    
    style.appendChild(document.createTextNode(content));
    
    const promise = new Promise((res, rej) => {
        style.onload = res;
        style.onerror = rej;
    });
    
    document.head.appendChild(style);
    
    await promise;
}
