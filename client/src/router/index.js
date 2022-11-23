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
      path: '/install',
      name: 'install',
      props: true,
      component: () => import('../components/Install')
    },
    {
      path: '/login',
      name: 'login',
      props: true,
      component: () => import('../components/Login')
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../components/Profile'),
      meta: { requiresAuth: true }
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('../components/Notifications'),
      meta: { requiresAuth: true }
    },
    {
      path: '/inventory',
      component: () => import('../components/inventory/Navigation'),
      meta: { requiresInventory: true },
      children: [
        {
          path: '',
          name: 'inventory',
          meta: { requiresInventory: true },
          redirect: { name: 'inventory.servers' }
        },
        {
          path: 'environments',
          name: 'inventory.environments',
          component: () => import('../components/inventory/views/Environments'),
          meta: { requiresInventory: true }
        },
        {
          path: 'regions',
          name: 'inventory.regions',
          component: () => import('../components/inventory/views/Regions'),
          meta: { requiresInventory: true }
        },
        {
          path: 'servers',
          name: 'inventory.servers',
          component: () => import('../components/inventory/views/Servers'),
          meta: { requiresInventory: true }
        },
        {
          path: 'auxiliary',
          name: 'inventory.auxiliary',
          component: () => import('../components/inventory/views/Auxiliary'),
          meta: { requiresInventory: true }
        },
        {
          path: 'cloud',
          name: 'inventory.cloud',
          component: () => import('../components/inventory/views/Cloud'),
          meta: { requiresInventory: true }
        }
      ]
    },
    {
      path: '/deployments',
      component: () => import('../components/deployments/Navigation'),
      meta: { requiresDeployments: true },
      children: [
        {
          path: '',
          name: 'deployments',
          component: () => import('../components/deployments/Deployments'),
          meta: { requiresDeployments: true }
        },
        {
          path: 'releases',
          name: 'deployments.releases',
          component: () => import('../components/deployments/Releases'),
          meta: { requiresDeployments: true }
        },
        {
          path: 'shared',
          name: 'deployments.shared',
          component: () => import('../components/deployments/Shared'),
          meta: { requiresDeployments: true }
        },
        {
          path: 'new/:mode/:uri?',
          name: 'deployments.new',
          component: () => import('../components/deployments/views/Navigation'),
          meta: { requiresDeployments: true }
        },
        {
          path: ':uri',
          name: 'deployments.execution',
          component: () => import('../components/deployments/Execution'),
          meta: { requiresDeployments: true }
        },
      ]
    },
    {
      path: '/results/:uri?',
      name: 'results',
      alias: ['/viewer'],
      component: () => import('../components/deployments/Results'),
      meta: { requiresAuth: true }
    },
    {
      path: '/monitoring',
      meta: { requiresMonitoring: true },
      component: () => import('../components/monitoring/Navigation'),
      children: [
        {
          path: '',
          name: 'monitoring',
          component: () => import('../components/monitoring/Monitoring'),
          meta: { requiresMonitoring: true }
        },
        {
          path: 'parameters',
          name: 'monitoring.parameters',
          component: () => import('../components/monitoring/views/Parameters'),
          meta: { requiresMonitoring: true }
        },
        {
          path: 'processlist',
          name: 'monitoring.processlist',
          component: () => import('../components/monitoring/views/Processlist'),
          meta: { requiresMonitoring: true }
        },
        {
          path: 'queries',
          name: 'monitoring.queries',
          component: () => import('../components/monitoring/views/Queries'),
          meta: { requiresMonitoring: true }
        }
      ]
    },
    {
      path: '/monitor',
      component: () => import('../components/monitoring/Navigation'),
      meta: { requiresMonitoring: true },
      children: [
        {
          path: ':id',
          name: 'monitor',
          component: () => import('../components/monitoring/Monitor'),
          meta: { requiresMonitoring: true }
        }
      ]
    },
    {
      path: '/utils',
      meta: { requiresUtils: true },
      component: () => import('../components/utils/Navigation'),
      children: [
        {
          path: '',
          name: 'utils',
          meta: { requiresUtils: true },
          redirect: { name: 'utils.imports' }
        },
        {
          path: 'imports',
          name: 'utils.imports',
          component: () => import('../components/utils/imports/Imports'),
          meta: { requiresUtils: true }
        },
        {
          path: 'imports/new',
          name: 'utils.imports.new',
          component: () => import('../components/utils/imports/New'),
          meta: { requiresUtils: true }
        },
        {
          path: 'imports/:uri',
          name: 'utils.imports.info',
          component: () => import('../components/utils/imports/Info'),
          meta: { requiresUtils: true }
        },
        {
          path: 'exports',
          name: 'utils.exports',
          component: () => import('../components/utils/exports/Exports'),
          meta: { requiresUtils: true }
        },
        {
          path: 'exports/new',
          name: 'utils.exports.new',
          component: () => import('../components/utils/exports/New'),
          meta: { requiresUtils: true }
        },
        {
          path: 'exports/:uri',
          name: 'utils.exports.info',
          component: () => import('../components/utils/exports/Info'),
          meta: { requiresUtils: true }
        },
        {
          path: 'clones',
          name: 'utils.clones',
          component: () => import('../components/utils/clones/Clones'),
          meta: { requiresUtils: true }
        },
        {
          path: 'clones/new',
          name: 'utils.clones.new',
          component: () => import('../components/utils/clones/New'),
          meta: { requiresUtils: true }
        },
        {
          path: 'clones/:uri',
          name: 'utils.clones.info',
          component: () => import('../components/utils/clones/Info'),
          meta: { requiresUtils: true }
        },
      ]
    },
    {
      path: '/client',
      meta: { requiresClient: true },
      component: () => import('../components/client/Navigation'),
      children: [
        {
          path: '',
          name: 'client',
          component: () => import('../components/client/Client'),
          meta: { requiresClient: true, keepAlive: true },
        }
      ]
    },
    {
      path: '/admin',
      component: () => import('../components/admin/Navigation'),
      meta: { requiresAdmin: true },
      children: [
        {
          path: '',
          name: 'admin',
          meta: { requiresAdmin: true },
          redirect: { name: 'admin.settings' }
        },
        {
          path: 'settings',
          name: 'admin.settings',
          alias: ["/admin/settings/license", "/admin/settings/sql", "/admin/settings/amazon", "/admin/settings/security", "/admin/settings/advanced"],
          component: () => import('../components/admin/views/Settings'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'users',
          name: 'admin.users',
          component: () => import('../components/admin/views/Users'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'groups',
          name: 'admin.groups',
          component: () => import('../components/admin/views/Groups'),
          meta: { requiresAdmin: true },
          children: [
            {
              path: ':id?/:mode',
              name: 'admin.group',
              component: () => import('../components/admin/views/Group'),
              meta: { requiresAdmin: true }
            }
          ]
        },
        {
          path: 'inventory',
          name: 'admin.inventory',
          alias: ["/admin/inventory/servers", "/admin/inventory/regions", "/admin/inventory/environments", "/admin/inventory/auxiliary", "/admin/inventory/cloud"],
          component: () => import('../components/admin/views/Inventory'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'deployments',
          name: 'admin.deployments',
          component: () => import('../components/admin/views/Deployments'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'monitoring',
          name: 'admin.monitoring',
          component: () => import('../components/admin/views/Monitoring'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'utils',
          name: 'admin.utils',
          alias: ["/admin/utils/imports", "/admin/utils/exports", "/admin/utils/clones"],
          component: () => import('../components/admin/views/Utils'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'client',
          name: 'admin.client',
          alias: ["/admin/client/queries", "/admin/client/servers"],
          component: () => import('../components/admin/views/Client'),
          meta: { requiresAdmin: true }
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  if (to.path == '/logout') store.dispatch('app/logout').then(() => next({ path: '/login' }))
  else if (to.path == '/login' && store.getters['app/isLoggedIn']) next('/')
  else if (to.matched.some(record => record.meta.requiresAdmin)) {
    if (store.getters['app/isLoggedIn'] && store.getters['app/admin']) next()
    else next({ path: '/' })
  }
  else if (to.matched.some(record => record.meta.requiresInventory)) {
    if (store.getters['app/isLoggedIn'] && store.getters['app/inventory_enabled']) next()
    else if (to.fullPath != '/') next({ path: '/login', query: { url: to.fullPath.substring(1) } })
    else next({ path: '/login' })
  }
  else if (to.matched.some(record => record.meta.requiresDeployments)) {
    if (store.getters['app/isLoggedIn'] && store.getters['app/deployments_enabled']) next()
    else if (to.fullPath != '/') next({ path: '/login', query: { url: to.fullPath.substring(1) } })
    else next({ path: '/login' })
  }
  else if (to.matched.some(record => record.meta.requiresMonitoring)) {
    if (store.getters['app/isLoggedIn'] && store.getters['app/monitoring_enabled']) next()
    else if (to.fullPath != '/') next({ path: '/login', query: { url: to.fullPath.substring(1) } })
    else next({ path: '/login' })
  }
  else if (to.matched.some(record => record.meta.requiresUtils)) {
    if (store.getters['app/isLoggedIn'] && store.getters['app/utils_enabled']) next()
    else if (to.fullPath != '/') next({ path: '/login', query: { url: to.fullPath.substring(1) } })
    else next({ path: '/login' })
  }
  else if (to.matched.some(record => record.meta.requiresClient)) {
    if (store.getters['app/isLoggedIn'] && store.getters['app/client_enabled']) next()
    else if (to.fullPath != '/') next({ path: '/login', query: { url: to.fullPath.substring(1) } })
    else next({ path: '/login' })
  }
  else if (to.matched.some(record => record.meta.requiresAuth)) {
    if (store.getters['app/isLoggedIn']) next()
    else if (to.fullPath != '/') next({ path: '/login', query: { url: to.fullPath.substring(1) } })
    else next({ path: '/login' })
  }
  else next()
})

export default router