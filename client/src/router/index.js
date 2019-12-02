import Vue from 'vue'
import VueRouter from 'vue-router'
import store from './../store'

Vue.use(VueRouter)

let router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../components/Home'),
      meta: { requiresAuth: true }  
    },
    {
      path: '/setup',
      name: 'setup',
      props: true,
      component: () => import('../components/Setup'),
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      props: true,
      component: () => import('../components/Login'),
      meta: { requiresAuth: false }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../components/Profile'),
      meta: { requiresAuth: true }
    },
    {
      path: '/results',
      name: 'results',
      component: () => import('../components/deployments/Results'),
      meta: { requiresAuth: true }
    },
    {
      path: '/results/:uri',
      name: 'results_uri',
      component: () => import('../components/deployments/Results'),
      meta: { requiresAuth: true }
    },
    {
      path: '/deployments',
      component: () => import('../components/deployments/Navigation'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'deployments',
          component: () => import('../components/deployments/Deployments'),
          meta: { requiresAuth: true }
        },
        {
          path: 'new',
          name: 'deployments.new',
          component: () => import('../components/deployments/views/Navigation'),
          meta: { requiresAuth: true }
        },
        {
          path: 'information',
          name: 'deployments.information',
          props: true,
          component: () => import('../components/deployments/Information'),
          meta: { requiresAuth: true }
        },
        {
          path: 'environments',
          name: 'deployments.environments',
          component: () => import('../components/deployments/settings/Environments'),
          meta: { requiresAuth: true }
        },
        {
          path: 'regions',
          name: 'deployments.regions',
          component: () => import('../components/deployments/settings/Regions'),
          meta: { requiresAuth: true }
        },
        {
          path: 'servers',
          name: 'deployments.servers',
          component: () => import('../components/deployments/settings/Servers'),
          meta: { requiresAuth: true }
        },
        {
          path: 'auxiliary',
          name: 'deployments.auxiliary',
          component: () => import('../components/deployments/settings/Auxiliary'),
          meta: { requiresAuth: true }
        },
        {
          path: 'slack',
          name: 'deployments.slack',
          component: () => import('../components/deployments/settings/Slack'),
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/monitoring',
      meta: { requiresAuth: true, requiresAdmin: false },
      component: () => import('../components/monitoring/Navigation'),
      children: [
        {
          path: '',
          name: 'monitoring',
          component: () => import('../components/monitoring/Monitoring'),
          meta: { requiresAuth: true }
        },
        {
          path: 'processlist',
          name: 'monitoring.processlist',
          component: () => import('../components/monitoring/views/Processlist'),
          meta: { requiresAuth: true }
        },
        {
          path: 'queries',
          name: 'monitoring.queries',
          component: () => import('../components/monitoring/views/Queries'),
          meta: { requiresAuth: true }
        }
      ]
    },
    {
      path: '/admin',
      component: () => import('../components/admin/Navigation'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'admin',
          component: () => import('../components/admin/Admin'),
          meta: { requiresAuth: true }
        },
        {
          path: 'settings',
          name: 'admin.settings',
          component: () => import('../components/admin/views/Settings'),
          meta: { requiresAuth: true }
        },
        {
          path: 'users',
          name: 'admin.users',
          component: () => import('../components/admin/views/Users'),
          meta: { requiresAuth: true }
        },
        {
          path: 'groups',
          name: 'admin.groups',
          component: () => import('../components/admin/views/Groups'),
          meta: { requiresAuth: true }
        },
        {
          path: 'groups/view',
          name: 'admin.groups.view',
          props: true,
          component: () => import('../components/admin/views/GroupsView'),
          meta: { requiresAuth: true }
        },
        {
          path: 'deployments',
          name: 'admin.deployments',
          component: () => import('../components/admin/views/Deployments'),
          meta: { requiresAuth: true }
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  if (to.path == '/login' && store.getters.isLoggedIn) next('/')
  else if (to.path == '/setup' && from.path == '/login') next('/')
  else if (to.matched.some(record => record.meta.requiresAuth)) {
    if (store.getters.isLoggedIn) next()
    else if (to.fullPath != '/') next({ path: '/login', query: { url: to.fullPath.substring(1) } })
    else next({ path: '/login' })
  } 
  else next()
})

export default router