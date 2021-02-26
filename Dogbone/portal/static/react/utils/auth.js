export const isLoggedIn = () => {
    return document.cookie.indexOf('user') >= 0;
}
