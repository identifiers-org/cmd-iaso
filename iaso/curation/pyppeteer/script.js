function (content, id, type = 'text/javascript') {
    if (document.getElementById(id) !== null) {
        return;
    }
    
    const script = document.createElement('script');
    
    let error = null;
    
    script.type = type;
    script.text = content;
    script.onerror = (e) => error = e;
    
    document.head.appendChild(script);
    
    if (error) {
        throw error;
    }
}
