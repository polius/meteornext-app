<template>
  <div>
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Query History</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-text-field ref="field" v-model="search" label="Filter..." solo dense clearable hide-details></v-text-field>
                <!-- <v-data-table></v-data-table> -->
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
::v-deep .v-label {
  font-size: 14px;
}
</style>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      dialog: false,
      search: '',
    }
  },
  computed: {
    ...mapFields([
      'history',
    ], { path: 'client/client' }),
  },
  mounted() {
    EventBus.$on('SHOW_HISTORY', this.showDialog);
  },
  methods: {
    showDialog() {
      this.search = ''
      this.dialog = true
      this.$nextTick(() => { this.$refs.field.focus() })
    }
  },
}
</script>