import { createRouter, createWebHistory } from 'vue-router'

import AdminEditor from '../views/AdminEditor.vue'
import AdminLogin from '../views/AdminLogin.vue'
import HomePage from '../views/HomePage.vue'
import ProfileEditor from '../views/ProfileEditor.vue'
import Connection from '../views/connection.vue'
import AdminInbox from '../views/AdminInbox.vue'
import PostDetail from '../views/PostDetail.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomePage },
    { path: '/posts/:id', name: 'post-detail', component: PostDetail },
    { path: '/admin/login', name: 'admin-login', component: AdminLogin },
    { path: '/admin/editor', name: 'admin-editor', component: AdminEditor },
    { path: '/admin/inbox', name: 'admin-inbox', component: AdminInbox },
    { path: '/profile', name: 'profile', component: ProfileEditor },
    { path: '/connection', name: 'connection', component: Connection },
  ],
})

export default router
