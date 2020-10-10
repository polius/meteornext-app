<template>
  <v-container fluid style="padding:0px;">
    <v-row ref="list" no-gutters style="height:calc(100% - 36px); overflow:auto;">
      <v-treeview :active.sync="sidebar" item-key="id" :open.sync="sidebarOpened" :items="rights['sidebar']" :search="sidebarSearch" activatable open-on-click transition class="clear_shadow" style="height:calc(100% - 62px); width:100%; overflow-y:auto;">
        <template v-slot:label="{item}">
          <v-btn @click="sidebarClick(item)" @contextmenu="onRightClick" text style="font-size:14px; text-transform:none; font-weight:400; width:100%; justify-content:left; padding-left:10px;"> 
            <v-icon v-if="'children' in item" small style="padding-right:10px">fas fa-user</v-icon>
            {{ item.name }}
            <v-spacer></v-spacer>
            <v-progress-circular v-if="rightsLoading && item.id == sidebar[0]" indeterminate size="16" width="2" color="white"></v-progress-circular>
          </v-btn>
        </template>
      </v-treeview>
      <v-text-field v-if="rights['sidebar'].length > 0" v-model="sidebarSearch" label="Search" dense solo hide-details height="38px" style="float:left; width:100%; padding:10px;"></v-text-field>
    </v-row>
    <v-row no-gutters style="height:35px; border-top:2px solid #3b3b3b; width:100%">
      <v-btn text small title="New User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn text small title="Delete User Right" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#3b3b3b; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
    </v-row>
  </v-container>
</template>

<style scoped src="@/styles/treeview.css"></style>

<style scoped>
.v-input__slot {
  background-color:#484848;
}
</style>

<script>
import { mapFields } from '../../../js/map-fields'
import EventBus from '../../../js/event-bus'

export default {
  data() {
    return {
      // Rights
      sidebar: [],
      sidebarSelected: {},
      sidebarOpened: [],
      sidebarSearch: '',
    }
  },
  computed: {
    ...mapFields([
      'rights',
      'rightsLoading',
    ], { path: 'client/connection' }),
  },
  methods: {
    sidebarClick(item) {
      if ('children' in item) return
      EventBus.$emit('GET_RIGHTS', item['user'], item['name'])
    },
    onRightClick(event) {
      event.preventDefault()
    }
  }
}
</script>