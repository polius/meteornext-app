<template>
  <div>
    <v-card>
      <v-container fluid grid-list-lg style="padding-top:10px;">
        <v-layout row wrap>
          <v-flex xs12>
            <v-form>
              <!-- METADATA -->
              <div class="title font-weight-regular" style="padding-top:10px;">Metadata</div>
              <v-text-field v-model="name" label="Name" hint="Example: Release v1.0.0" required dark></v-text-field>

              <!-- EXECUTION -->
              <div class="title font-weight-regular" style="margin-top:10px;margin-bottom:20px;">Execution</div>
              <codemirror v-model="code" :options="cmOptions"></codemirror>

              <!-- PARAMETERS -->
              <div class="title font-weight-regular" style="margin-top:20px;">Parameters</div>
              <v-select v-model="environment" :items="environment_items" label="Environment" required></v-select>
              <v-radio-group v-model="execution_mode" style="margin-top:0px;">
                <template v-slot:label>
                  <div>Select the <strong>Execution Mode</strong>:</div>
                </template>
                <v-radio value="validation" color="success">
                  <template v-slot:label>
                    <div class="success--text">Validation</div>
                  </template>
                </v-radio>
                <v-radio value="test" color="orange">
                  <template v-slot:label>
                    <div class="orange--text">Test Execution</div>
                  </template>
                </v-radio>
                <v-radio value="deploy" color="red">
                  <template v-slot:label>
                    <div class="red--text">Deployment</div>
                  </template>
                </v-radio>
              </v-radio-group>

              <v-radio-group v-model="execution_method" style="margin-top:0px; padding-top:0px;">
                <template v-slot:label>
                  <div>Select the <strong>Execution Method</strong>:</div>
                </template>
                <v-radio value="parallel">
                  <template v-slot:label>
                    <div>Parallel</div>
                  </template>
                </v-radio>
                <v-radio value="sequential">
                  <template v-slot:label>
                    <div>Sequential</div>
                  </template>
                </v-radio>
              </v-radio-group>

              <v-text-field v-if="execution_method=='parallel'" v-model="threads" label="Threads" dark style="margin-top:0px; padding-top:0px; margin-bottom:5px;"></v-text-field>

              <v-btn color="success" dark style="margin-left:0px;">Deploy</v-btn>
              <router-link to="/deployments"><v-btn color="error" dark style="margin-left:0px;">Cancel</v-btn></router-link>

            </v-form>
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" flat @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<style>
.CodeMirror {
  min-height:500px;
}
</style>

<script>
import { codemirror } from 'vue-codemirror'
import 'codemirror/lib/codemirror.css'

// language
import 'codemirror/mode/python/python.js'
// theme css
import 'codemirror/theme/monokai.css'

// require active-line.js
import 'codemirror/addon/selection/active-line.js'
// closebrackets
import 'codemirror/addon/edit/closebrackets.js'
// keyMap
import 'codemirror/mode/clike/clike.js'
import 'codemirror/addon/edit/matchbrackets.js'
import 'codemirror/addon/comment/comment.js'
import 'codemirror/addon/dialog/dialog.js'
import 'codemirror/addon/dialog/dialog.css'
import 'codemirror/addon/search/searchcursor.js'
import 'codemirror/addon/search/search.js'
import 'codemirror/keymap/sublime.js'

export default {
  data() {
    return {
      // Metadata
      name: '',

      // Execution
      environment: '',
      environment_items: [],

      // Code
      code: '',

      cmOptions: {
        autoCloseBrackets: true,
        styleActiveLine: true,
        lineNumbers: true,
        line: true,
        mode: 'python',
        theme: 'monokai',
        keyMap: 'sublime',
        extraKeys: { "Tab": function(cm) { cm.replaceSelection("    " , "end"); }}
      },

      // Parameters
      execution_mode: '',
      execution_method: 'parallel',
      threads: '10',

      // Query Dialog
      queryDialog: false,
      queryDialogTitle: '',
      
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: {
    codemirror
  },
  methods: {
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    queryDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script>